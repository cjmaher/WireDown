WITH CTE_AGENCY_EVENT AS
(
  SELECT
    NUM_1
    , TO_DATE(SUBSTR(COALESCE(off_dts,ad_ts),1,14),'YYYYMMDDHH24MISS') as off_dts
 --   , TRUNC((TO_DATE(SUBSTR(COALESCE(off_dts,ad_ts),1,14),'YYYYMMDDHH24MISS')-1) - to_date('1-1-1970 00:00:00','MM-DD-YYYY HH24:Mi:SS'))*24*3600 as epoch_date_start
 --   , TRUNC((TO_DATE(SUBSTR(COALESCE(off_dts,ad_ts),1,14),'YYYYMMDDHH24MISS')+1) - to_date('1-1-1970 00:00:00','MM-DD-YYYY HH24:Mi:SS'))*24*3600 as epoch_date_end
    , decode(trsource_A, 'B', 'Batch - Auto Created.', 'C', 'Cust Service Rep', 'V', 'VRU/IVR', 'W', 'Web (CSO)', 'P', 'PSTR (for Police/Fire departments)', 'L', 'Streetlight Outage Reporting', 'A', 'AMI', 'M', 'Mobile App', 'O', 'Downtime Electric', 'I', 'InService reported', 'S', 'SMS - Job Auto Created', 'Internal') as Event_Creation_Type
    , FEEDER
    , TYCOD
    , PHASE
    , METER_A
    , AECUST1
    , EID
    , DGROUP AS SC
    , IS_OPEN
    , to_date(substr(XDTS,1,14),'YYYYMMDDHH24MISS') as XDTS
  FROM
    AGENCY_EVENT@INSERVICE
  WHERE
    FEEDER IS NOT NULL
    AND IS_OPEN='T'
),
CTE_COMMS AS
(
   SELECT a.EID, upper(a.COMM) COMM
   FROM
     EVCOM@INSERVICE a
     , CTE_AGENCY_EVENT b 
   WHERE
     a.EID=b.EID
     AND b.TYCOD='PPWD'
     AND a.CSEC BETWEEN TRUNC( ((SYSDATE-2) - DATE '1970-01-01') * 86400 ) AND TRUNC( ((SYSDATE+2) - DATE '1970-01-01') * 86400 )
)
SELECT 
  * 
FROM (
  SELECT
    MAIN.NUM_1 EVENT_NUMBER,
    MAIN.FEEDER CIRCUIT,
    MAIN.SC SERVICE_CENTER,
    to_char(MAIN.OFF_DTS,'YYYY-MM-DD hh24:mi:ss') as EVENT_CREATION_TIME,
    CASE WHEN W.RESULT = 1 THEN 'Likely Wiredown' WHEN W.RESULT = 0 THEN 'Likely Non Wiredown' ELSE 'TBD' END AS PRIORITY,
    COALESCE(SIG_XFMRS.ALARMS, 0) AS AMI_ALARM,
    Main.Event_Creation_Type CHANNEL,
    LOCATIONS,
    COUNT(DISTINCT OTHER.NUM_1) AS CIRCUIT_EVENTS,
    MAIN.EID,
    MAX(CASE WHEN COMMS.COMM LIKE ('%IS IT DOWN NEAR A SCHOOL, PARK OR PLAYGROUND?:YES%') THEN 1 ELSE 0 END) AS SCHOOL_PARK,
    MAX(CASE WHEN COMMS.COMM LIKE ('%ARE POLICE AND FIRE STANDING BY?:YES%') OR COMM LIKE ('%WHAT IS ON FIRE?%WIRE%') THEN 1 ELSE 0 END) AS PF,
    MAX(CASE WHEN COMMS.COMM LIKE ('%WILL YOU REMAIN AT THE SITE UNTIL DTE ENERGY ARRIVES? YES%') THEN  1 ELSE 0 END) AS PF_SITE,
    MAX(CASE WHEN COMMS.COMM LIKE ('%IS THE POWER OUT TO THE SITE? YES%') OR COMM LIKE ('%IS YOUR POWER OUT? : YES%') OR COMM LIKE ('%DO YOU HAVE POWER?:NO%')THEN 1 ELSE 0 END) AS POWER_OUT,
    MAX(CASE WHEN COMMS.COMM LIKE ('% ARC%') AND UPPER(COMM) NOT LIKE ('%. NO%ARC%') THEN 1 ELSE 0 END) AS WIRES_ARC,
    MAX(CASE WHEN COMMS.COMM LIKE ('% BURN%') AND UPPER(COMM) NOT LIKE ('% BURNED%') THEN 1 ELSE 0 END) AS BURN,
    MAX(CASE WHEN COMMS.COMM LIKE ('% PRIMARY%') THEN 1 ELSE 0 END) AS PRIMARY_WIRE,                                   
    MAX(CASE WHEN COMMS.COMM LIKE ('% TAP%AREA%') THEN 1 ELSE 0 END) AS AREA_TAPED
  FROM
    (
      SELECT
         A.*,
         P.XFMR AS REPORTED_XFMR,
         TO_CHAR(OFF_DTS-1, 'YYYY-MM-DD HH24:MI:SS') AS CLOUD_DATE,
         TO_CHAR(OFF_DTS,'YYYYMM') AS P_DATE,
         CASE WHEN A.AECUST1 IS NULL THEN ADDRESS.ELOCATION ELSE A.AECUST1 END AS LOCATIONS
       FROM
       (      
         SELECT
           NUM_1,
           off_dts,
 --          epoch_date_start,
 --          epoch_date_end,
           Event_Creation_Type,
           FEEDER,
           TYCOD,
           PHASE,
           METER_A,
           AECUST1,
           EID,
           SC,
           XDTS
         FROM
           CTE_AGENCY_EVENT
         WHERE
           is_open = 'T'
           AND TYCOD = 'PPWD'
           AND (FEEDER IS NOT NULL AND FEEDER <> 'NULL' AND FEEDER <> 'PLD') 
       ) A
       LEFT JOIN CISPERSL2@INSERVICE P ON (P.METER_NUM=A.METER_A)
       LEFT JOIN COMMON_EVENT@INSERVICE ADDRESS ON(ADDRESS.EID=A.EID)
     ) MAIN
     --LEFT JOIN EVCOM@INSERVICE COMMS ON (MAIN.EID=COMMS.EID AND to_date(substr(COMMS.CDTS,1,14), 'YYYYMMDDHH24MISS') between (MAIN.OFF_DTS) and (MAIN.OFF_DTS+1))
     LEFT JOIN CTE_COMMS COMMS ON (MAIN.EID=COMMS.EID)-- AND COMMS.CSEC between  MAIN.epoch_date_start and MAIN.epoch_date_end)
     LEFT JOIN INTOXDM.WD_PRED_RESULTS W ON (W.NUM_1 = MAIN.NUM_1)
     LEFT JOIN(    
       SELECT
         NUM_1,
         OFF_DTS,
         FEEDER,
         TYCOD,
         PHASE,
         METER_A,
         AECUST1,
         EID,
         XDTS
       FROM 
        CTE_AGENCY_EVENT
       WHERE 
        is_open = 'T'
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
    ) OTHER ON OTHER.FEEDER = MAIN.FEEDER AND OTHER.NUM_1 <> MAIN.NUM_1 AND (OTHER.OFF_DTS >= MAIN.OFF_DTS - INTERVAL '12' HOUR)
    LEFT JOIN(
        SELECT
            NUM_1,
            SUM(METERS) AS ALARMS,
            SUM(VOLTRMS_ABOVE) AS VOLTRMS_ABOVE,
            SUM(VOLTRMS_BELOW) AS VOLTRMS_BELOW
        FROM(
        SELECT *
        FROM AMIDM.WD_SIG_XFMRS
        WHERE (NUM_1, XFMR) NOT IN (
            SELECT NUM_1, XFMR 
            FROM AMIDM.WD_SIG_XFMRS
            WHERE POWERDOWN = 0
            AND METERS/nullif(TOTAL_CUST,0) < .5
        )
        )
        --WHERE DISTANCE <= 500
        --AND POWERDOWN <> 0
        GROUP BY NUM_1
   ) SIG_XFMRS ON (SIG_XFMRS.NUM_1 = MAIN.NUM_1)
  
  GROUP BY MAIN.NUM_1,
    MAIN.FEEDER,
    MAIN.OFF_DTS,
    MAIN.Event_Creation_Type, 
    MAIN.SC,
    SIG_XFMRS.ALARMS,
    LOCATIONS,
    MAIN.EID,
    W.RESULT
)
WHERE 
  PRIORITY IS NOT NULL
ORDER BY
  EVENT_CREATION_TIME DESC