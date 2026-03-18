{\rtf1\ansi\ansicpg1252\cocoartf2759
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fmodern\fcharset0 Courier-Bold;\f1\fmodern\fcharset0 Courier;}
{\colortbl;\red255\green255\blue255;\red16\green121\blue2;\red173\green173\blue173;\red19\green112\blue166;
\red38\green38\blue38;\red67\green67\blue67;\red170\green0\blue83;\red12\green95\blue24;\red255\green236\blue236;
\red0\green0\blue0;\red9\green80\blue173;\red134\green83\blue39;\red0\green0\blue213;}
{\*\expandedcolortbl;;\cssrgb\c0\c53333\c0;\cssrgb\c73333\c73333\c73333;\cssrgb\c5490\c51765\c70980;
\cssrgb\c20000\c20000\c20000;\cssrgb\c33333\c33333\c33333;\cssrgb\c73333\c0\c40000;\cssrgb\c0\c43922\c12549;\cssrgb\c100000\c94118\c94118;
\cssrgb\c0\c0\c0;\cssrgb\c0\c40000\c73333;\cssrgb\c60000\c40000\c20000;\cssrgb\c0\c0\c86667;}
\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\deftab720
\pard\pardeftab720\partightenfactor0

\f0\b\fs26 \cf2 \expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 from
\f1\b0 \cf3 \strokec3  
\f0\b \cf4 \strokec4 __future__
\f1\b0 \cf3 \strokec3  
\f0\b \cf2 \strokec2 import
\f1\b0 \cf5 \strokec5  annotations\
\

\f0\b \cf2 \strokec2 import
\f1\b0 \cf3 \strokec3  
\f0\b \cf4 \strokec4 re
\f1\b0 \cf5 \strokec5 \

\f0\b \cf2 \strokec2 from
\f1\b0 \cf3 \strokec3  
\f0\b \cf4 \strokec4 dataclasses
\f1\b0 \cf3 \strokec3  
\f0\b \cf2 \strokec2 import
\f1\b0 \cf5 \strokec5  dataclass\

\f0\b \cf2 \strokec2 from
\f1\b0 \cf3 \strokec3  
\f0\b \cf4 \strokec4 datetime
\f1\b0 \cf3 \strokec3  
\f0\b \cf2 \strokec2 import
\f1\b0 \cf5 \strokec5  datetime, timezone\

\f0\b \cf2 \strokec2 from
\f1\b0 \cf3 \strokec3  
\f0\b \cf4 \strokec4 typing
\f1\b0 \cf3 \strokec3  
\f0\b \cf2 \strokec2 import
\f1\b0 \cf5 \strokec5  Any, Dict, List\
\
\
\pard\pardeftab720\partightenfactor0

\f0\b \cf6 \strokec6 @dataclass
\f1\b0 \cf5 \strokec5 \
\pard\pardeftab720\partightenfactor0

\f0\b \cf2 \strokec2 class
\f1\b0 \cf3 \strokec3  
\f0\b \cf7 \strokec7 LicenseStatus
\f1\b0 \cf5 \strokec5 :\
    account_id: \cf8 \strokec8 str\cf5 \strokec5 \
    authorized: \cf8 \strokec8 bool\cf5 \strokec5 \
    reason: \cf8 \strokec8 str\cf5 \strokec5 \
    valid_until: datetime | 
\f0\b \cf2 \strokec2 None
\f1\b0 \cf5 \strokec5  = 
\f0\b \cf2 \strokec2 None
\f1\b0 \cf5 \strokec5 \
\
\
LICENSE_TABLE: Dict[\cf8 \strokec8 str\cf5 \strokec5 , \cf8 \strokec8 str\cf5 \strokec5 ] = \{\
    \cf5 \cb9 \strokec5 "demo_account_1"\cf5 \cb1 \strokec5 : \cf5 \cb9 \strokec5 "2026-12-31T23:59:59+00:00"\cf5 \cb1 \strokec5 ,\
    \cf5 \cb9 \strokec5 "partner_account_alpha"\cf5 \cb1 \strokec5 : \cf5 \cb9 \strokec5 "2026-06-30T23:59:59+00:00"\cf5 \cb1 \strokec5 ,\
    \cf5 \cb9 \strokec5 "wesley_admin"\cf5 \cb1 \strokec5 : \cf5 \cb9 \strokec5 "2099-12-31T23:59:59+00:00"\cf5 \cb1 \strokec5 ,\
\}\
\
TRIGGER_PATTERNS: List[\cf8 \strokec8 str\cf5 \strokec5 ] = [\
    \cf5 \cb9 \strokec5 r"\\bEP\\s*/\\s*Trigger1\\b"\cf5 \cb1 \strokec5 ,\
    \cf5 \cb9 \strokec5 r"\\bEP\\s*/\\s*Trigger\\s*One\\b"\cf5 \cb1 \strokec5 ,\
    \cf5 \cb9 \strokec5 r"\\bEnergetic\\s+Paradigm\\s*/\\s*Trigger1\\b"\cf5 \cb1 \strokec5 ,\
]\
\
_TRIGGER_REGEXES = [re.compile(p, re.IGNORECASE) 
\f0\b \cf2 \strokec2 for
\f1\b0 \cf5 \strokec5  p 
\f0\b \cf5 \strokec10 in
\f1\b0 \cf5 \strokec5  TRIGGER_PATTERNS]\
\
\

\f0\b \cf2 \strokec2 def
\f1\b0 \cf3 \strokec3  
\f0\b \cf11 \strokec11 parse_iso_datetime
\f1\b0 \cf5 \strokec5 (value: \cf8 \strokec8 str\cf5 \strokec5 ) -> datetime:\
    dt = datetime.fromisoformat(value)\
    
\f0\b \cf2 \strokec2 if
\f1\b0 \cf5 \strokec5  dt.tzinfo 
\f0\b \cf5 \strokec10 is
\f1\b0 \cf5 \strokec5  
\f0\b \cf2 \strokec2 None
\f1\b0 \cf5 \strokec5 :\
        dt = dt.replace(tzinfo=timezone.utc)\
    
\f0\b \cf2 \strokec2 return
\f1\b0 \cf5 \strokec5  dt.astimezone(timezone.utc)\
\
\

\f0\b \cf2 \strokec2 def
\f1\b0 \cf3 \strokec3  
\f0\b \cf11 \strokec11 check_license
\f1\b0 \cf5 \strokec5 (account_id: \cf8 \strokec8 str\cf5 \strokec5 , now: datetime) -> LicenseStatus:\
    
\f0\b \cf2 \strokec2 if
\f1\b0 \cf5 \strokec5  account_id 
\f0\b \cf5 \strokec10 not
\f1\b0 \cf5 \strokec5  
\f0\b \cf5 \strokec10 in
\f1\b0 \cf5 \strokec5  LICENSE_TABLE:\
        
\f0\b \cf2 \strokec2 return
\f1\b0 \cf5 \strokec5  LicenseStatus(\
            account_id=account_id,\
            authorized=
\f0\b \cf2 \strokec2 False
\f1\b0 \cf5 \strokec5 ,\
            reason=\cf5 \cb9 \strokec5 "account_not_authorized"\cf5 \cb1 \strokec5 ,\
            valid_until=
\f0\b \cf2 \strokec2 None
\f1\b0 \cf5 \strokec5 ,\
        )\
\
    valid_until = parse_iso_datetime(LICENSE_TABLE[account_id])\
    
\f0\b \cf2 \strokec2 if
\f1\b0 \cf5 \strokec5  now.astimezone(timezone.utc) > valid_until:\
        
\f0\b \cf2 \strokec2 return
\f1\b0 \cf5 \strokec5  LicenseStatus(\
            account_id=account_id,\
            authorized=
\f0\b \cf2 \strokec2 False
\f1\b0 \cf5 \strokec5 ,\
            reason=\cf5 \cb9 \strokec5 "license_expired"\cf5 \cb1 \strokec5 ,\
            valid_until=valid_until,\
        )\
\
    
\f0\b \cf2 \strokec2 return
\f1\b0 \cf5 \strokec5  LicenseStatus(\
        account_id=account_id,\
        authorized=
\f0\b \cf2 \strokec2 True
\f1\b0 \cf5 \strokec5 ,\
        reason=\cf5 \cb9 \strokec5 "authorized"\cf5 \cb1 \strokec5 ,\
        valid_until=valid_until,\
    )\
\
\

\f0\b \cf2 \strokec2 def
\f1\b0 \cf3 \strokec3  
\f0\b \cf11 \strokec11 detect_trigger
\f1\b0 \cf5 \strokec5 (query: \cf8 \strokec8 str\cf5 \strokec5 ) -> \cf8 \strokec8 bool\cf5 \strokec5 :\
    
\f0\b \cf2 \strokec2 return
\f1\b0 \cf5 \strokec5  \cf8 \strokec8 any\cf5 \strokec5 (regex.search(query) 
\f0\b \cf2 \strokec2 for
\f1\b0 \cf5 \strokec5  regex 
\f0\b \cf5 \strokec10 in
\f1\b0 \cf5 \strokec5  _TRIGGER_REGEXES)\
\
\

\f0\b \cf2 \strokec2 def
\f1\b0 \cf3 \strokec3  
\f0\b \cf11 \strokec11 strip_trigger
\f1\b0 \cf5 \strokec5 (query: \cf8 \strokec8 str\cf5 \strokec5 ) -> \cf8 \strokec8 str\cf5 \strokec5 :\
    cleaned = query\
    
\f0\b \cf2 \strokec2 for
\f1\b0 \cf5 \strokec5  regex 
\f0\b \cf5 \strokec10 in
\f1\b0 \cf5 \strokec5  _TRIGGER_REGEXES:\
        cleaned = regex.sub(\cf5 \cb9 \strokec5 ""\cf5 \cb1 \strokec5 , cleaned)\
    
\f0\b \cf2 \strokec2 return
\f1\b0 \cf5 \strokec5  cleaned.strip()\
\
\

\f0\b \cf2 \strokec2 class
\f1\b0 \cf3 \strokec3  
\f0\b \cf7 \strokec7 EPEngineDemo
\f1\b0 \cf5 \strokec5 :\
    
\f0\b \cf2 \strokec2 def
\f1\b0 \cf3 \strokec3  
\f0\b \cf11 \strokec11 interpret
\f1\b0 \cf5 \strokec5 (\cf8 \strokec8 self\cf5 \strokec5 , query: \cf8 \strokec8 str\cf5 \strokec5 ) -> Dict[\cf8 \strokec8 str\cf5 \strokec5 , Any]:\
        
\f0\b \cf2 \strokec2 return
\f1\b0 \cf5 \strokec5  \{\
            \cf5 \cb9 \strokec5 "raw_query"\cf5 \cb1 \strokec5 : query,\
            \cf5 \cb9 \strokec5 "problem_framing"\cf5 \cb1 \strokec5 : query,\
        \}\
\
    
\f0\b \cf2 \strokec2 def
\f1\b0 \cf3 \strokec3  
\f0\b \cf11 \strokec11 decompose_energy
\f1\b0 \cf5 \strokec5 (\cf8 \strokec8 self\cf5 \strokec5 , interpreted: Dict[\cf8 \strokec8 str\cf5 \strokec5 , Any]) -> Dict[\cf8 \strokec8 str\cf5 \strokec5 , Any]:\
        
\f0\b \cf2 \strokec2 return
\f1\b0 \cf5 \strokec5  \{\
            \cf5 \cb9 \strokec5 "energy_units"\cf5 \cb1 \strokec5 : [\
                \cf5 \cb9 \strokec5 "computational energy"\cf5 \cb1 \strokec5 ,\
                \cf5 \cb9 \strokec5 "informational energy"\cf5 \cb1 \strokec5 ,\
                \cf5 \cb9 \strokec5 "decision energy"\cf5 \cb1 \strokec5 ,\
                \cf5 \cb9 \strokec5 "temporal energy"\cf5 \cb1 \strokec5 ,\
            ],\
            \cf5 \cb9 \strokec5 "constraints"\cf5 \cb1 \strokec5 : [\
                \cf5 \cb9 \strokec5 "authorization"\cf5 \cb1 \strokec5 ,\
                \cf5 \cb9 \strokec5 "time validity"\cf5 \cb1 \strokec5 ,\
            ],\
            \cf5 \cb9 \strokec5 "goal"\cf5 \cb1 \strokec5 : \cf5 \cb9 \strokec5 "produce official EP-structured analysis"\cf5 \cb1 \strokec5 ,\
            \cf5 \cb9 \strokec5 "input"\cf5 \cb1 \strokec5 : interpreted,\
        \}\
\
    
\f0\b \cf2 \strokec2 def
\f1\b0 \cf3 \strokec3  
\f0\b \cf11 \strokec11 reason_energy_flow
\f1\b0 \cf5 \strokec5 (\cf8 \strokec8 self\cf5 \strokec5 , decomposition: Dict[\cf8 \strokec8 str\cf5 \strokec5 , Any]) -> Dict[\cf8 \strokec8 str\cf5 \strokec5 , Any]:\
        
\f0\b \cf2 \strokec2 return
\f1\b0 \cf5 \strokec5  \{\
            \cf5 \cb9 \strokec5 "flow_analysis"\cf5 \cb1 \strokec5 : \cf5 \cb9 \strokec5 "Input is routed through a controlled EP process stub."\cf5 \cb1 \strokec5 ,\
            \cf5 \cb9 \strokec5 "bottlenecks"\cf5 \cb1 \strokec5 : [\
                \cf5 \cb9 \strokec5 "full decomposition logic not yet implemented"\cf5 \cb1 \strokec5 ,\
                \cf5 \cb9 \strokec5 "full reconfiguration logic not yet implemented"\cf5 \cb1 \strokec5 ,\
            ],\
            \cf5 \cb9 \strokec5 "structure_reconfiguration"\cf5 \cb1 \strokec5 : [\
                \cf5 \cb9 \strokec5 "replace stub reasoning with domain-aware EP modules"\cf5 \cb1 \strokec5 ,\
                \cf5 \cb9 \strokec5 "connect to official private prompt templates or orchestration layer"\cf5 \cb1 \strokec5 ,\
            ],\
            \cf5 \cb9 \strokec5 "input"\cf5 \cb1 \strokec5 : decomposition,\
        \}\
\
    
\f0\b \cf2 \strokec2 def
\f1\b0 \cf3 \strokec3  
\f0\b \cf11 \strokec11 synthesize
\f1\b0 \cf5 \strokec5 (\cf8 \strokec8 self\cf5 \strokec5 , reasoning: Dict[\cf8 \strokec8 str\cf5 \strokec5 , Any], license_status: LicenseStatus) -> Dict[\cf8 \strokec8 str\cf5 \strokec5 , Any]:\
        
\f0\b \cf2 \strokec2 return
\f1\b0 \cf5 \strokec5  \{\
            \cf5 \cb9 \strokec5 "ep_activation"\cf5 \cb1 \strokec5 : 
\f0\b \cf2 \strokec2 True
\f1\b0 \cf5 \strokec5 ,\
            \cf5 \cb9 \strokec5 "trigger"\cf5 \cb1 \strokec5 : \cf5 \cb9 \strokec5 "EP/Trigger1"\cf5 \cb1 \strokec5 ,\
            \cf5 \cb9 \strokec5 "license"\cf5 \cb1 \strokec5 : \{\
                \cf5 \cb9 \strokec5 "account_id"\cf5 \cb1 \strokec5 : license_status.account_id,\
                \cf5 \cb9 \strokec5 "valid_until"\cf5 \cb1 \strokec5 : license_status.valid_until.isoformat() 
\f0\b \cf2 \strokec2 if
\f1\b0 \cf5 \strokec5  license_status.valid_until 
\f0\b \cf2 \strokec2 else
\f1\b0 \cf5 \strokec5  
\f0\b \cf2 \strokec2 None
\f1\b0 \cf5 \strokec5 ,\
            \},\
            \cf5 \cb9 \strokec5 "structured_output"\cf5 \cb1 \strokec5 : \{\
                \cf5 \cb9 \strokec5 "problem_framing"\cf5 \cb1 \strokec5 : reasoning[\cf5 \cb9 \strokec5 "input"\cf5 \cb1 \strokec5 ][\cf5 \cb9 \strokec5 "input"\cf5 \cb1 \strokec5 ][\cf5 \cb9 \strokec5 "problem_framing"\cf5 \cb1 \strokec5 ],\
                \cf5 \cb9 \strokec5 "energy_units"\cf5 \cb1 \strokec5 : reasoning[\cf5 \cb9 \strokec5 "input"\cf5 \cb1 \strokec5 ][\cf5 \cb9 \strokec5 "energy_units"\cf5 \cb1 \strokec5 ],\
                \cf5 \cb9 \strokec5 "constraints_and_goals"\cf5 \cb1 \strokec5 : \{\
                    \cf5 \cb9 \strokec5 "constraints"\cf5 \cb1 \strokec5 : reasoning[\cf5 \cb9 \strokec5 "input"\cf5 \cb1 \strokec5 ][\cf5 \cb9 \strokec5 "constraints"\cf5 \cb1 \strokec5 ],\
                    \cf5 \cb9 \strokec5 "goal"\cf5 \cb1 \strokec5 : reasoning[\cf5 \cb9 \strokec5 "input"\cf5 \cb1 \strokec5 ][\cf5 \cb9 \strokec5 "goal"\cf5 \cb1 \strokec5 ],\
                \},\
                \cf5 \cb9 \strokec5 "energy_flow_analysis"\cf5 \cb1 \strokec5 : reasoning[\cf5 \cb9 \strokec5 "flow_analysis"\cf5 \cb1 \strokec5 ],\
                \cf5 \cb9 \strokec5 "bottlenecks"\cf5 \cb1 \strokec5 : reasoning[\cf5 \cb9 \strokec5 "bottlenecks"\cf5 \cb1 \strokec5 ],\
                \cf5 \cb9 \strokec5 "structure_reconfiguration"\cf5 \cb1 \strokec5 : reasoning[\cf5 \cb9 \strokec5 "structure_reconfiguration"\cf5 \cb1 \strokec5 ],\
                \cf5 \cb9 \strokec5 "actionable_conclusion"\cf5 \cb1 \strokec5 : \cf5 \cb9 \strokec5 "Official EP demo route completed successfully."\cf5 \cb1 \strokec5 ,\
            \},\
        \}\
\
    
\f0\b \cf2 \strokec2 def
\f1\b0 \cf3 \strokec3  
\f0\b \cf11 \strokec11 run
\f1\b0 \cf5 \strokec5 (\cf8 \strokec8 self\cf5 \strokec5 , query: \cf8 \strokec8 str\cf5 \strokec5 , license_status: LicenseStatus) -> Dict[\cf8 \strokec8 str\cf5 \strokec5 , Any]:\
        interpreted = \cf8 \strokec8 self\cf5 \strokec5 .interpret(query)\
        decomposition = \cf8 \strokec8 self\cf5 \strokec5 .decompose_energy(interpreted)\
        reasoning = \cf8 \strokec8 self\cf5 \strokec5 .reason_energy_flow(decomposition)\
        
\f0\b \cf2 \strokec2 return
\f1\b0 \cf5 \strokec5  \cf8 \strokec8 self\cf5 \strokec5 .synthesize(reasoning, license_status)\
\
\

\f0\b \cf2 \strokec2 def
\f1\b0 \cf3 \strokec3  
\f0\b \cf11 \strokec11 route_request
\f1\b0 \cf5 \strokec5 (account_id: \cf8 \strokec8 str\cf5 \strokec5 , query: \cf8 \strokec8 str\cf5 \strokec5 , now: datetime | 
\f0\b \cf2 \strokec2 None
\f1\b0 \cf5 \strokec5  = 
\f0\b \cf2 \strokec2 None
\f1\b0 \cf5 \strokec5 ) -> Dict[\cf8 \strokec8 str\cf5 \strokec5 , Any]:\
    current_time = now 
\f0\b \cf5 \strokec10 or
\f1\b0 \cf5 \strokec5  datetime.now(timezone.utc)\
    license_status = check_license(account_id=account_id, now=current_time)\
    trigger_detected = detect_trigger(query)\
\
    
\f0\b \cf2 \strokec2 if
\f1\b0 \cf5 \strokec5  
\f0\b \cf5 \strokec10 not
\f1\b0 \cf5 \strokec5  trigger_detected:\
        
\f0\b \cf2 \strokec2 return
\f1\b0 \cf5 \strokec5  \{\
            \cf5 \cb9 \strokec5 "mode"\cf5 \cb1 \strokec5 : \cf5 \cb9 \strokec5 "standard"\cf5 \cb1 \strokec5 ,\
            \cf5 \cb9 \strokec5 "authorized"\cf5 \cb1 \strokec5 : license_status.authorized,\
            \cf5 \cb9 \strokec5 "trigger_detected"\cf5 \cb1 \strokec5 : 
\f0\b \cf2 \strokec2 False
\f1\b0 \cf5 \strokec5 ,\
            \cf5 \cb9 \strokec5 "result"\cf5 \cb1 \strokec5 : \{\
                \cf5 \cb9 \strokec5 "message"\cf5 \cb1 \strokec5 : \cf5 \cb9 \strokec5 "Processed outside official EP route."\cf5 \cb1 \strokec5 ,\
                \cf5 \cb9 \strokec5 "reason"\cf5 \cb1 \strokec5 : license_status.reason,\
                \cf5 \cb9 \strokec5 "query"\cf5 \cb1 \strokec5 : query,\
            \},\
        \}\
\
    
\f0\b \cf2 \strokec2 if
\f1\b0 \cf5 \strokec5  
\f0\b \cf5 \strokec10 not
\f1\b0 \cf5 \strokec5  license_status.authorized:\
        
\f0\b \cf2 \strokec2 return
\f1\b0 \cf5 \strokec5  \{\
            \cf5 \cb9 \strokec5 "mode"\cf5 \cb1 \strokec5 : \cf5 \cb9 \strokec5 "standard"\cf5 \cb1 \strokec5 ,\
            \cf5 \cb9 \strokec5 "authorized"\cf5 \cb1 \strokec5 : 
\f0\b \cf2 \strokec2 False
\f1\b0 \cf5 \strokec5 ,\
            \cf5 \cb9 \strokec5 "trigger_detected"\cf5 \cb1 \strokec5 : 
\f0\b \cf2 \strokec2 True
\f1\b0 \cf5 \strokec5 ,\
            \cf5 \cb9 \strokec5 "result"\cf5 \cb1 \strokec5 : \{\
                \cf5 \cb9 \strokec5 "message"\cf5 \cb1 \strokec5 : \cf5 \cb9 \strokec5 "Official EP trigger detected, but authorization failed."\cf5 \cb1 \strokec5 ,\
                \cf5 \cb9 \strokec5 "reason"\cf5 \cb1 \strokec5 : license_status.reason,\
            \},\
        \}\
\
    engine = EPEngineDemo()\
    cleaned_query = strip_trigger(query)\
\
    
\f0\b \cf2 \strokec2 return
\f1\b0 \cf5 \strokec5  \{\
        \cf5 \cb9 \strokec5 "mode"\cf5 \cb1 \strokec5 : \cf5 \cb9 \strokec5 "official_ep"\cf5 \cb1 \strokec5 ,\
        \cf5 \cb9 \strokec5 "authorized"\cf5 \cb1 \strokec5 : 
\f0\b \cf2 \strokec2 True
\f1\b0 \cf5 \strokec5 ,\
        \cf5 \cb9 \strokec5 "trigger_detected"\cf5 \cb1 \strokec5 : 
\f0\b \cf2 \strokec2 True
\f1\b0 \cf5 \strokec5 ,\
        \cf5 \cb9 \strokec5 "result"\cf5 \cb1 \strokec5 : engine.run(cleaned_query, license_status),\
    \}\
\
\

\f0\b \cf2 \strokec2 if
\f1\b0 \cf5 \strokec5  \cf12 \strokec12 __name__\cf5 \strokec5  == \cf5 \cb9 \strokec5 "__main__"\cf5 \cb1 \strokec5 :\
    demo_now = datetime(
\f0\b \cf13 \strokec13 2026
\f1\b0 \cf5 \strokec5 , 
\f0\b \cf13 \strokec13 3
\f1\b0 \cf5 \strokec5 , 
\f0\b \cf13 \strokec13 9
\f1\b0 \cf5 \strokec5 , 
\f0\b \cf13 \strokec13 12
\f1\b0 \cf5 \strokec5 , 
\f0\b \cf13 \strokec13 0
\f1\b0 \cf5 \strokec5 , 
\f0\b \cf13 \strokec13 0
\f1\b0 \cf5 \strokec5 , tzinfo=timezone.utc)\
    sample_query = \cf5 \cb9 \strokec5 "EP / Trigger1 Analyze low-compute AI reasoning efficiency."\cf5 \cb1 \strokec5 \
    response = route_request(\
        account_id=\cf5 \cb9 \strokec5 "demo_account_1"\cf5 \cb1 \strokec5 ,\
        query=sample_query,\
        now=demo_now,\
    )\
    
\f0\b \cf2 \strokec2 from
\f1\b0 \cf3 \strokec3  
\f0\b \cf4 \strokec4 pprint
\f1\b0 \cf3 \strokec3  
\f0\b \cf2 \strokec2 import
\f1\b0 \cf5 \strokec5  pprint\
    pprint(response)\
}