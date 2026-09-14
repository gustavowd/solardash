import unittest
from pathlib import Path
from datetime import date, timedelta
from unittest.mock import MagicMock, patch
import pandas as pd
from streamlit.testing.v1 import AppTest
from monitoring import counter_daily, energy, power
from periods import preset_dates, month_end
from analysis import variable_catalog


class MonitoringTests(unittest.TestCase):
    def test_years_preset_sums_each_year(self):
        conn = MagicMock()
        conn.query.return_value = pd.DataFrame({
            'device_id': [1], 'device_name': ['Inversor'], 'device_type': [1],
        })
        readings = pd.Series([10., 20., 40.], index=pd.to_datetime([
            '2024-04-01', '2024-12-01', '2025-02-01',
        ]))
        with patch('streamlit.connection', return_value=conn), \
                patch('monitoring.energy', return_value=readings), \
                patch('monitoring.render_chart') as render:
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'Totalizadores.py'))
            app.session_state.monitor_period = (date(2024, 1, 1), date(2025, 12, 31))
            app.session_state.period_applied_preset = 'Período de Meses'
            app.run()
            self.assertEqual(app.selectbox(key='monitor_grouping').value, 'Mês')
            app.session_state.period_applied_preset = 'Anos'
            app.run()
            self.assertFalse(app.exception)
            self.assertEqual(app.selectbox(key='monitor_grouping').value, 'Ano')
            fig = render.call_args.args[0]
            self.assertEqual(list(fig.data[0].x), ['2024', '2025'])
            self.assertEqual(list(fig.data[0].y), [30., 40.])
            self.assertEqual(fig.layout.xaxis.type, 'category')

    def test_catalog_does_not_scan_measurements(self):
        conn = MagicMock()
        variable_catalog(conn)
        sql = conn.query.call_args.args[0]
        self.assertIn('FROM measurement_type', sql)
        self.assertNotIn('measurements', sql)

    def test_pandas_database_error_shows_retry(self):
        conn = MagicMock()
        conn.query.side_effect = pd.errors.DatabaseError('statement timeout')
        with patch('streamlit.connection', return_value=conn):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'Totalizadores.py')).run()
            self.assertFalse(app.exception)
            self.assertTrue(app.error)
            self.assertTrue(any(button.label == 'Tentar novamente' for button in app.button))

    def test_period_boundaries(self):
        self.assertEqual(preset_dates('Mês Anterior', date(2026, 1, 3)), (date(2025, 12, 1), date(2025, 12, 31)))
        self.assertEqual(preset_dates('Últimos 7 Dias', date(2026, 1, 3)), (date(2025, 12, 28), date(2026, 1, 3)))
        self.assertEqual(month_end(date(2024, 2, 1)), date(2024, 2, 29))


    def test_power_converts_watts_to_kw(self):
        conn = MagicMock()
        conn.query.return_value = pd.DataFrame({
            'time': pd.to_datetime(['2026-09-11 14:35'] * 2),
            'device_id': [2, 3], 'value': [75000., 916.88],
        })
        result = power(conn, [2, 3], 27, date(2026, 9, 11), date(2026, 9, 11), 1000)
        self.assertAlmostEqual(result.iloc[0], 75.91688)

    def test_counter_reset_is_missing(self):
        frame = pd.DataFrame({'time': ['2026-01-01 01:00', '2026-01-01 23:00', '2026-01-02 01:00', '2026-01-02 23:00'],
                              'device_id': [1]*4, 'value': [10, 30, 30, 2]})
        result = counter_daily(frame)
        self.assertEqual(result.iloc[0], 20)
        self.assertTrue(pd.isna(result.iloc[1]))

    def test_query_bounds_and_current_day_fallback(self):
        conn = MagicMock()
        conn.query.return_value = pd.DataFrame()
        power(conn, [1], 0, date(2026, 1, 1), date(2026, 1, 1), 1000)
        self.assertEqual(conn.query.call_args.kwargs['params']['end'], date(2026, 1, 2))
        energy(conn, [1], 1, date(2026, 1, 1), date(2026, 1, 31))
        sql = conn.query.call_args.args[0]
        self.assertIn('NOT EXISTS', sql)
        self.assertIn('d.device_id=m.device_id', sql)
        self.assertIn('UNION ALL', sql)

    def test_monitor_series_period_and_navigation(self):
        conn = MagicMock()
        today = date.today()
        def query(sql, **kwargs):
            if 'FROM devices' in sql:
                return pd.DataFrame({'device_id':[1, 2, 3], 'device_name':['Inversor', 'Medidor', 'Geral'], 'device_type':[1, 2, 3]})
            if 'FROM measurement_type' in sql:
                return pd.DataFrame({'measurement_type_id':[10], 'measurement_name':['Potência geral']})
            return pd.DataFrame({'time':pd.to_datetime([str(today)+' 10:00', str(today)+' 11:00']), 'device_id':[1, 1], 'measurement_type_id':[10, 10], 'value':[1000., 2000.]})
        conn.query.side_effect = query
        with patch('streamlit.connection', return_value=conn):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'Totalizadores.py')).run()
            self.assertFalse(app.exception)
            self.assertTrue(app.sidebar.get('page_link'))
            app.checkbox(key='enabled_2').check().run()
            app.checkbox(key='enabled_3').check().run()
            app.selectbox(key='general_variable_True').set_value(10)
            app.selectbox(key='general_unit_True').set_value('W').run()
            self.assertFalse(app.exception)
            import json
            spec = json.loads(app.get('plotly_chart')[0].proto.spec)
            self.assertEqual(len(spec['data']), 3)
            self.assertTrue(all(trace['type']=='scatter' for trace in spec['data']))
            app.button(key='open_period').click().run()
            app.button(key='preset_Últimos 7 Dias').click().run()
            self.assertEqual(app.session_state.monitor_period, (today, today))
            next(button for button in app.button if button.label == 'Cancelar').click().run()
            self.assertEqual(app.session_state.monitor_period, (today, today))
            app.button(key='open_period').click().run()
            self.assertEqual(app.session_state.period_draft_preset, 'Hoje')
            app.button(key='preset_Período de Dias').click().run()
            app.date_input(key='period_days').set_value((today-timedelta(days=90), today)).run()
            next(button for button in app.button if button.label == 'Aplicar').click().run()
            self.assertFalse(app.exception)
            spec = json.loads(app.get('plotly_chart')[0].proto.spec)
            self.assertTrue(all(trace['type']=='bar' for trace in spec['data']))
            app.segmented_control[0].set_value('Analisar').run()
            self.assertFalse(app.exception)
            app.multiselect(key='analysis_variables').set_value([10]).run()
            self.assertNotIn('analysis_applied', app.session_state)
            app.button(key='FormSubmitter:analysis_selection-Aplicar seleção').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.metric), 6)
            self.assertEqual(app.metric[0].value, '2.000,00')
            app.multiselect(key='analysis_equipment').set_value([]).run()
            self.assertEqual(app.session_state.analysis_applied, ([1], [10]))
            self.assertEqual(len(app.metric), 6)
            app.button(key='FormSubmitter:analysis_selection-Aplicar seleção').click().run()
            self.assertEqual(app.session_state.analysis_applied, ([], [10]))
            self.assertEqual(len(app.get('plotly_chart')), 0)
            app.multiselect(key='analysis_equipment').set_value([1])
            app.button(key='FormSubmitter:analysis_selection-Aplicar seleção').click().run()
            spec = json.loads(app.get('plotly_chart')[0].proto.spec)
            self.assertTrue(all(trace['type']=='scatter' for trace in spec['data']))


if __name__ == '__main__':
    unittest.main()
