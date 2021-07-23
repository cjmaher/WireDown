import pandas as pd
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph as P
from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import Table as T
from reportlab.platypus.tables import TableStyle
import sqlite3  # development

# from sqlalchemy import create_engine  #  production
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.urls import reverse

pd.set_option('expand_frame_repr', False)  # for debugging and printings df
db_to_col_keys = {'NUM_1': 'Event Number',
                  'FEEDER': 'Circuit',
                  'SC': 'Service Center',
                  'TYCOD': 'Outage Type', # per line 179 of dashboard2.php
                  'OFF_DTS': 'Event Creation Time',
                  'PRIORITY': 'Priority',
                  'ALARMS': 'AMI Alarm',
                  '???': 'Comments',
                  'EVENT_CREATION_TYPE': 'CHANNEL',
                  'LOCATIONS': 'Location',
                  'OTHER_EVENTS': 'Circuit Events'}


class NumberedSimpleDocTemplate(SimpleDocTemplate):
    def after_page(self):
        self.canv.saveState()
        self.canv.setLineWidth(1)
        self.canv.line(0.5 * inch, 0.6 * inch, self.width + 0.5 * inch, 0.6 * inch)
        self.canv.drawCentredString(self.width * 0.55, 0.4 * inch, 'Page {0}'.format(self.page))


def tooltip(request):
    return None


def events_modal(request):
    return None


def gen_csv(request):
    print('csv link works')
    return redirect(reverse_lazy('events:events'))


def wire_down_events(request):
    query = '''
                    SELECT *
                        FROM (SELECT MAIN.NUM_1,
                                     MAIN.FEEDER,
                                     MAIN.TYCOD,
                                     to_char(MAIN.OFF_DTS, 'mm/dd/yyyy hh24:mi:ss')                      as OFF_DTS,
                                     Main.Event_Creation_Type,
                                     MAIN.SC,
                                     to_char(MAIN.XDTS, 'mm/dd/yyyy hh24:mi:ss')                         as XDTS,
                                     COUNT(DISTINCT OTHER.NUM_1)                                         AS OTHER_EVENTS,
                                     CASE WHEN SIG_XFMRS.ALARMS IS NULL THEN 0 ELSE SIG_XFMRS.ALARMS END AS ALARMS,
                                     MAIN.EID,
                                     CASE
                                         WHEN W.RESULT = 1 THEN 'Likely Wiredown'
                                         WHEN W.RESULT = 0 THEN 'Likely Non Wiredown'
                                         ELSE 'TBD' END                                                  AS PRIORITY,
                                     LOCATIONS
                              FROM (
                                       SELECT A.*,
                                              P.XFMR                                                                AS REPORTED_XFMR,
                                              TO_CHAR(OFF_DTS - 1, 'YYYY-MM-DD HH24:MI:SS')                         AS CLOUD_DATE,
                                              TO_CHAR(OFF_DTS, 'YYYYMM')                                            AS P_DATE,
                                              CASE WHEN A.AECUST1 IS NULL THEN ADDRESS.ELOCATION ELSE A.AECUST1 END AS LOCATIONS
                                       FROM (
                                                SELECT NUM_1,
                                                       to_date(substr(decode(off_dts, null, ad_Ts, off_dts), 1, 14),
                                                               'YYYYMMDDHH24MISS')                      as off_dts,
                                                       decode(trsource_A, 'B', 'Batch - Auto Created.', 'C', 'Cust Service Rep', 'V',
                                                              'VRU/IVR', 'W', 'Web (CSO)', 'P', 'PSTR (for Police/Fire departments)', 'L',
                                                              'Streetlight Outage Reporting', 'A', 'AMI', 'M', 'Mobile App', 'O',
                                                              'Downtime Electric', 'I', 'InService reported', 'S', 'SMS - Job Auto Created',
                                                              'Internal')                               as Event_Creation_Type,
                                                       FEEDER,
                                                       TYCOD,
                                                       PHASE,
                                                       METER_A,
                                                       AECUST1,
                                                       EID,
                                                       DGROUP                                           AS SC,
                                                       --SUBSTR(DGROUP,0,3) AS SC,
                                                       to_date(substr(XDTS, 1, 14), 'YYYYMMDDHH24MISS') as XDTS
                                                FROM AGENCY_EVENT@INSERVICE
                                                WHERE is_open = 'T'
                                                  AND TYCOD IN ('PPWD')
                                                  AND (FEEDER IS NOT NULL AND FEEDER <> 'NULL' AND FEEDER <> 'PLD') --------------------------------------------------------------------DECIDE IF SHOWING ON DASHBOARD
                                                --AND to_date(substr(decode(off_dts,null,ad_Ts,off_dts),1,14),'YYYYMMDDHH24MISS') >= TO_DATE('06/14/2020 20:00','MM/DD/YYYY HH24:MI')
                                                --AND to_date(substr(decode(off_dts,null,ad_Ts,off_dts),1,14),'YYYYMMDDHH24MISS') <= TO_DATE('06/16/2020 11:00','MM/DD/YYYY HH24:MI')
                                            ) A
                                                lEFT JOIN(
                                           SELECT *
                                           FROM CISPERSL2@INSERVICE
                                       ) P ON P.METER_NUM = A.METER_A
                                                LEFT JOIN(
                                           SELECT EID, ELOCATION
                                           FROM COMMON_EVENT@INSERVICE
                                       ) ADDRESS ON ADDRESS.EID = A.EID
                                   ) MAIN
                                       LEFT JOIN INTOXDM.WD_PRED_RESULTS W ON W.NUM_1 = MAIN.NUM_1
                                       LEFT JOIN(
                                  SELECT NUM_1,
                                         to_date(substr(decode(off_dts, null, ad_Ts, off_dts), 1, 14), 'YYYYMMDDHH24MISS') as off_dts,
                                         FEEDER,
                                         TYCOD,
                                         PHASE,
                                         METER_A,
                                         AECUST1,
                                         EID,
                                         SUBSTR(DGROUP, 0, 3)                                                              AS SC,
                                         to_date(substr(XDTS, 1, 14), 'YYYYMMDDHH24MISS')                                  as XDTS
                                  FROM AGENCY_EVENT@INSERVICE
                                  WHERE is_open = 'T'
                                    and TYCOD IN ('CP',
                                                  'FUSE',
                                                  'ISO',
                                                  'OHCKT',
                                                  'OHTRANS',
                                                  'ONELEG',
                                                  'RECLO',
                                                  'SDXL',
                                                  'UGCKT',
                                                  'UGPSC',
                                                  'UGTRANS',
                                                  'XCURR',
                                                  'CUTCOND',
                                                  'OHSWC',
                                                  'OHDS',
                                                  'UGFUSE',
                                                  'UGDS')
                              ) OTHER ON OTHER.FEEDER = MAIN.FEEDER AND OTHER.NUM_1 <> MAIN.NUM_1 AND
                                         (OTHER.OFF_DTS >= MAIN.OFF_DTS - INTERVAL '24' HOUR)
                                       LEFT JOIN(
                                  SELECT NUM_1,
                                         SUM(METERS)        AS ALARMS,
                                         SUM(VOLTRMS_ABOVE) AS VOLTRMS_ABOVE,
                                         SUM(VOLTRMS_BELOW) AS VOLTRMS_BELOW
                                  FROM (
                                           SELECT *
                                           FROM AMIDM.WD_SIG_XFMRS
                                           WHERE (NUM_1, XFMR) NOT IN (
                                               SELECT NUM_1, XFMR
                                               FROM AMIDM.WD_SIG_XFMRS
                                               WHERE POWERDOWN = 0
                                                 AND METERS / nullif(TOTAL_CUST, 0) < .5
                                           )
                                       )
                                       --WHERE DISTANCE <= 500
                                       --AND POWERDOWN <> 0
                                  GROUP BY NUM_1
                              )
                    '''
    # db_conn = create_engine('oracle+cx_oracle://{user}:{password}@{ip_address}:1521/{schema}') # production
    db_conn = sqlite3.connect('/Users/macuser/PycharmProjects/WireDown/db.sqlite3')
    # df = pd.read_sql_query(query, db_conn)  # production
    df = pd.read_sql_query('select * from main.events', db_conn)  # developmnet
    df.reset_index(drop=True, inplace=True)
    df = df.drop(['id'], axis=1)
    context = {'df': df}
    return render(request, 'events/event_view.html', context)


def gen_pdf(request):
    print('pdf link works')
    return redirect(reverse_lazy('events:events'))


class WireDownView(TemplateView):
    template_name = 'events/event_view.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        db_conn = sqlite3.connect('/Users/macuser/PycharmProjects/WireDown/db.sqlite3')
        df = pd.read_sql_query('select * from main.events', db_conn)  # developmnet
        df.reset_index(drop=True, inplace=True)
        df = df.drop(['id'], axis=1)
        context['df'] = df
        print(df)
        return context

    @staticmethod
    def gen_pdf(self, request):
        print('pdf link works')
        print(self.df)
        return redirect(reverse_lazy('events:events'))





