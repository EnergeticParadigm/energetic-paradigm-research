{\rtf1\ansi\ansicpg1252\cocoartf2759
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fmodern\fcharset0 Courier-Bold;\f1\fmodern\fcharset0 Courier;}
{\colortbl;\red255\green255\blue255;\red16\green121\blue2;\red173\green173\blue173;\red19\green112\blue166;
\red38\green38\blue38;\red255\green236\blue236;\red0\green0\blue0;\red9\green80\blue173;\red12\green95\blue24;
}
{\*\expandedcolortbl;;\cssrgb\c0\c53333\c0;\cssrgb\c73333\c73333\c73333;\cssrgb\c5490\c51765\c70980;
\cssrgb\c20000\c20000\c20000;\cssrgb\c100000\c94118\c94118;\cssrgb\c0\c0\c0;\cssrgb\c0\c40000\c73333;\cssrgb\c0\c43922\c12549;
}
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
\f0\b \cf4 \strokec4 datetime
\f1\b0 \cf3 \strokec3  
\f0\b \cf2 \strokec2 import
\f1\b0 \cf5 \strokec5  datetime\

\f0\b \cf2 \strokec2 from
\f1\b0 \cf3 \strokec3  
\f0\b \cf4 \strokec4 typing
\f1\b0 \cf3 \strokec3  
\f0\b \cf2 \strokec2 import
\f1\b0 \cf5 \strokec5  Any, Dict\
\

\f0\b \cf2 \strokec2 from
\f1\b0 \cf3 \strokec3  
\f0\b \cf4 \strokec4 license_check
\f1\b0 \cf3 \strokec3  
\f0\b \cf2 \strokec2 import
\f1\b0 \cf5 \strokec5  LicenseStatus, check_license\
\
TRIGGER_PATTERNS = [\
    \cf5 \cb6 \strokec5 r"\\bEP\\s*/\\s*Trigger1\\b"\cf5 \cb1 \strokec5 ,\
    \cf5 \cb6 \strokec5 r"\\bEP\\s*/\\s*Trigger\\s*One\\b"\cf5 \cb1 \strokec5 ,\
    \cf5 \cb6 \strokec5 r"\\bEnergetic\\s+Paradigm\\s*/\\s*Trigger1\\b"\cf5 \cb1 \strokec5 ,\
]\
\
_TRIGGER_REGEXES = [re.compile(p, re.IGNORECASE) 
\f0\b \cf2 \strokec2 for
\f1\b0 \cf5 \strokec5  p 
\f0\b \cf5 \strokec7 in
\f1\b0 \cf5 \strokec5  TRIGGER_PATTERNS]\
\
\

\f0\b \cf2 \strokec2 def
\f1\b0 \cf3 \strokec3  
\f0\b \cf8 \strokec8 detect_trigger
\f1\b0 \cf5 \strokec5 (query: \cf9 \strokec9 str\cf5 \strokec5 ) -> \cf9 \strokec9 bool\cf5 \strokec5 :\
    
\f0\b \cf2 \strokec2 return
\f1\b0 \cf5 \strokec5  \cf9 \strokec9 any\cf5 \strokec5 (regex.search(query) 
\f0\b \cf2 \strokec2 for
\f1\b0 \cf5 \strokec5  regex 
\f0\b \cf5 \strokec7 in
\f1\b0 \cf5 \strokec5  _TRIGGER_REGEXES)\
\
\

\f0\b \cf2 \strokec2 def
\f1\b0 \cf3 \strokec3  
\f0\b \cf8 \strokec8 _standard_route
\f1\b0 \cf5 \strokec5 (query: \cf9 \strokec9 str\cf5 \strokec5 , license_status: LicenseStatus) -> Dict[\cf9 \strokec9 str\cf5 \strokec5 , Any]:\
    
\f0\b \cf2 \strokec2 return
\f1\b0 \cf5 \strokec5  \{\
        \cf5 \cb6 \strokec5 "mode"\cf5 \cb1 \strokec5 : \cf5 \cb6 \strokec5 "standard"\cf5 \cb1 \strokec5 ,\
        \cf5 \cb6 \strokec5 "authorized"\cf5 \cb1 \strokec5 : license_status.authorized,\
        \cf5 \cb6 \strokec5 "trigger_detected"\cf5 \cb1 \strokec5 : detect_trigger(query),\
        \cf5 \cb6 \strokec5 "result"\cf5 \cb1 \strokec5 : \{\
            \cf5 \cb6 \strokec5 "message"\cf5 \cb1 \strokec5 : \cf5 \cb6 \strokec5 "Processed outside official EP route."\cf5 \cb1 \strokec5 ,\
            \cf5 \cb6 \strokec5 "reason"\cf5 \cb1 \strokec5 : license_status.reason,\
            \cf5 \cb6 \strokec5 "query"\cf5 \cb1 \strokec5 : query,\
        \},\
    \}\
\
\

\f0\b \cf2 \strokec2 def
\f1\b0 \cf3 \strokec3  
\f0\b \cf8 \strokec8 _official_ep_route
\f1\b0 \cf5 \strokec5 (query: \cf9 \strokec9 str\cf5 \strokec5 , license_status: LicenseStatus) -> Dict[\cf9 \strokec9 str\cf5 \strokec5 , Any]:\
    cleaned_query = query\
    
\f0\b \cf2 \strokec2 for
\f1\b0 \cf5 \strokec5  regex 
\f0\b \cf5 \strokec7 in
\f1\b0 \cf5 \strokec5  _TRIGGER_REGEXES:\
        cleaned_query = regex.sub(\cf5 \cb6 \strokec5 ""\cf5 \cb1 \strokec5 , cleaned_query).strip()\
\
    
\f0\b \cf2 \strokec2 return
\f1\b0 \cf5 \strokec5  \{\
        \cf5 \cb6 \strokec5 "mode"\cf5 \cb1 \strokec5 : \cf5 \cb6 \strokec5 "official_ep"\cf5 \cb1 \strokec5 ,\
        \cf5 \cb6 \strokec5 "authorized"\cf5 \cb1 \strokec5 : 
\f0\b \cf2 \strokec2 True
\f1\b0 \cf5 \strokec5 ,\
        \cf5 \cb6 \strokec5 "trigger_detected"\cf5 \cb1 \strokec5 : 
\f0\b \cf2 \strokec2 True
\f1\b0 \cf5 \strokec5 ,\
        \cf5 \cb6 \strokec5 "result"\cf5 \cb1 \strokec5 : \{\
            \cf5 \cb6 \strokec5 "ep_activation"\cf5 \cb1 \strokec5 : 
\f0\b \cf2 \strokec2 True
\f1\b0 \cf5 \strokec5 ,\
            \cf5 \cb6 \strokec5 "trigger"\cf5 \cb1 \strokec5 : \cf5 \cb6 \strokec5 "EP/Trigger1"\cf5 \cb1 \strokec5 ,\
            \cf5 \cb6 \strokec5 "message"\cf5 \cb1 \strokec5 : \cf5 \cb6 \strokec5 "Official EP route activated."\cf5 \cb1 \strokec5 ,\
            \cf5 \cb6 \strokec5 "structured_output"\cf5 \cb1 \strokec5 : \{\
                \cf5 \cb6 \strokec5 "problem_framing"\cf5 \cb1 \strokec5 : cleaned_query,\
                \cf5 \cb6 \strokec5 "energy_units"\cf5 \cb1 \strokec5 : [\
                    \cf5 \cb6 \strokec5 "computational energy"\cf5 \cb1 \strokec5 ,\
                    \cf5 \cb6 \strokec5 "informational energy"\cf5 \cb1 \strokec5 ,\
                    \cf5 \cb6 \strokec5 "decision energy"\cf5 \cb1 \strokec5 ,\
                    \cf5 \cb6 \strokec5 "temporal energy"\cf5 \cb1 \strokec5 ,\
                ],\
                \cf5 \cb6 \strokec5 "constraints_and_goals"\cf5 \cb1 \strokec5 : \{\
                    \cf5 \cb6 \strokec5 "goal"\cf5 \cb1 \strokec5 : \cf5 \cb6 \strokec5 "derive structured EP analysis"\cf5 \cb1 \strokec5 ,\
                    \cf5 \cb6 \strokec5 "constraints"\cf5 \cb1 \strokec5 : [\cf5 \cb6 \strokec5 "authorization"\cf5 \cb1 \strokec5 , \cf5 \cb6 \strokec5 "trigger validity"\cf5 \cb1 \strokec5 ],\
                \},\
                \cf5 \cb6 \strokec5 "energy_flow_analysis"\cf5 \cb1 \strokec5 : \cf5 \cb6 \strokec5 "Stub analysis placeholder."\cf5 \cb1 \strokec5 ,\
                \cf5 \cb6 \strokec5 "bottlenecks"\cf5 \cb1 \strokec5 : [\cf5 \cb6 \strokec5 "to be implemented in EP engine"\cf5 \cb1 \strokec5 ],\
                \cf5 \cb6 \strokec5 "structure_reconfiguration"\cf5 \cb1 \strokec5 : \cf5 \cb6 \strokec5 "to be implemented in EP engine"\cf5 \cb1 \strokec5 ,\
                \cf5 \cb6 \strokec5 "actionable_conclusion"\cf5 \cb1 \strokec5 : \cf5 \cb6 \strokec5 "Gateway and trigger logic succeeded."\cf5 \cb1 \strokec5 ,\
            \},\
            \cf5 \cb6 \strokec5 "license"\cf5 \cb1 \strokec5 : \{\
                \cf5 \cb6 \strokec5 "account_id"\cf5 \cb1 \strokec5 : license_status.account_id,\
                \cf5 \cb6 \strokec5 "valid_until"\cf5 \cb1 \strokec5 : license_status.valid_until.isoformat() 
\f0\b \cf2 \strokec2 if
\f1\b0 \cf5 \strokec5  license_status.valid_until 
\f0\b \cf2 \strokec2 else
\f1\b0 \cf5 \strokec5  
\f0\b \cf2 \strokec2 None
\f1\b0 \cf5 \strokec5 ,\
            \},\
        \},\
    \}\
\
\

\f0\b \cf2 \strokec2 def
\f1\b0 \cf3 \strokec3  
\f0\b \cf8 \strokec8 route_request
\f1\b0 \cf5 \strokec5 (account_id: \cf9 \strokec9 str\cf5 \strokec5 , query: \cf9 \strokec9 str\cf5 \strokec5 , now: datetime) -> Dict[\cf9 \strokec9 str\cf5 \strokec5 , Any]:\
    license_status = check_license(account_id=account_id, now=now)\
    trigger_detected = detect_trigger(query)\
\
    
\f0\b \cf2 \strokec2 if
\f1\b0 \cf5 \strokec5  
\f0\b \cf5 \strokec7 not
\f1\b0 \cf5 \strokec5  trigger_detected:\
        
\f0\b \cf2 \strokec2 return
\f1\b0 \cf5 \strokec5  _standard_route(query, license_status)\
\
    
\f0\b \cf2 \strokec2 if
\f1\b0 \cf5 \strokec5  
\f0\b \cf5 \strokec7 not
\f1\b0 \cf5 \strokec5  license_status.authorized:\
        
\f0\b \cf2 \strokec2 return
\f1\b0 \cf5 \strokec5  \{\
            \cf5 \cb6 \strokec5 "mode"\cf5 \cb1 \strokec5 : \cf5 \cb6 \strokec5 "standard"\cf5 \cb1 \strokec5 ,\
            \cf5 \cb6 \strokec5 "authorized"\cf5 \cb1 \strokec5 : 
\f0\b \cf2 \strokec2 False
\f1\b0 \cf5 \strokec5 ,\
            \cf5 \cb6 \strokec5 "trigger_detected"\cf5 \cb1 \strokec5 : 
\f0\b \cf2 \strokec2 True
\f1\b0 \cf5 \strokec5 ,\
            \cf5 \cb6 \strokec5 "result"\cf5 \cb1 \strokec5 : \{\
                \cf5 \cb6 \strokec5 "message"\cf5 \cb1 \strokec5 : \cf5 \cb6 \strokec5 "Official EP trigger detected, but authorization failed."\cf5 \cb1 \strokec5 ,\
                \cf5 \cb6 \strokec5 "reason"\cf5 \cb1 \strokec5 : license_status.reason,\
            \},\
        \}\
\
    
\f0\b \cf2 \strokec2 return
\f1\b0 \cf5 \strokec5  _official_ep_route(query, license_status)\
}