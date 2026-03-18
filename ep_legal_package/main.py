{\rtf1\ansi\ansicpg1252\cocoartf2759
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fmodern\fcharset0 Courier-Bold;\f1\fmodern\fcharset0 Courier;}
{\colortbl;\red255\green255\blue255;\red16\green121\blue2;\red173\green173\blue173;\red19\green112\blue166;
\red38\green38\blue38;\red255\green236\blue236;\red170\green0\blue83;\red12\green95\blue24;\red9\green80\blue173;
\red0\green0\blue0;\red251\green0\blue7;\red0\green0\blue213;\red234\green234\blue234;\red67\green67\blue67;
}
{\*\expandedcolortbl;;\cssrgb\c0\c53333\c0;\cssrgb\c73333\c73333\c73333;\cssrgb\c5490\c51765\c70980;
\cssrgb\c20000\c20000\c20000;\cssrgb\c100000\c94118\c94118;\cssrgb\c73333\c0\c40000;\cssrgb\c0\c43922\c12549;\cssrgb\c0\c40000\c73333;
\cssrgb\c0\c0\c0;\cssrgb\c100000\c0\c0;\cssrgb\c0\c0\c86667;\cssrgb\c93333\c93333\c93333;\cssrgb\c33333\c33333\c33333;
}
\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\deftab720
\pard\pardeftab720\partightenfactor0

\f0\b\fs26 \cf2 \expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 from
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
\f1\b0 \cf5 \strokec5  Any, Dict\
\

\f0\b \cf2 \strokec2 from
\f1\b0 \cf3 \strokec3  
\f0\b \cf4 \strokec4 fastapi
\f1\b0 \cf3 \strokec3  
\f0\b \cf2 \strokec2 import
\f1\b0 \cf5 \strokec5  FastAPI, HTTPException\

\f0\b \cf2 \strokec2 from
\f1\b0 \cf3 \strokec3  
\f0\b \cf4 \strokec4 pydantic
\f1\b0 \cf3 \strokec3  
\f0\b \cf2 \strokec2 import
\f1\b0 \cf5 \strokec5  BaseModel, Field\
\

\f0\b \cf2 \strokec2 from
\f1\b0 \cf3 \strokec3  
\f0\b \cf4 \strokec4 trigger_router
\f1\b0 \cf3 \strokec3  
\f0\b \cf2 \strokec2 import
\f1\b0 \cf5 \strokec5  route_request\
\
app = FastAPI(title=\cf5 \cb6 \strokec5 "EP Gateway"\cf5 \cb1 \strokec5 , version=\cf5 \cb6 \strokec5 "0.1.0"\cf5 \cb1 \strokec5 )\
\
\

\f0\b \cf2 \strokec2 class
\f1\b0 \cf3 \strokec3  
\f0\b \cf7 \strokec7 AnalyzeRequest
\f1\b0 \cf5 \strokec5 (BaseModel):\
    account_id: \cf8 \strokec8 str\cf5 \strokec5  = Field(..., description=\cf5 \cb6 \strokec5 "Authorized account identifier"\cf5 \cb1 \strokec5 )\
    query: \cf8 \strokec8 str\cf5 \strokec5  = Field(..., description=\cf5 \cb6 \strokec5 "User input"\cf5 \cb1 \strokec5 )\
    now_utc: \cf8 \strokec8 str\cf5 \strokec5  | 
\f0\b \cf2 \strokec2 None
\f1\b0 \cf5 \strokec5  = Field(\
        default=
\f0\b \cf2 \strokec2 None
\f1\b0 \cf5 \strokec5 ,\
        description=\cf5 \cb6 \strokec5 "Optional ISO datetime override for testing, e.g. 2026-03-09T12:00:00+00:00"\cf5 \cb1 \strokec5 ,\
    )\
\
\

\f0\b \cf2 \strokec2 class
\f1\b0 \cf3 \strokec3  
\f0\b \cf7 \strokec7 AnalyzeResponse
\f1\b0 \cf5 \strokec5 (BaseModel):\
    mode: \cf8 \strokec8 str\cf5 \strokec5 \
    authorized: \cf8 \strokec8 bool\cf5 \strokec5 \
    trigger_detected: \cf8 \strokec8 bool\cf5 \strokec5 \
    result: Dict[\cf8 \strokec8 str\cf5 \strokec5 , Any]\
\
\

\f0\b \cf2 \strokec2 def
\f1\b0 \cf3 \strokec3  
\f0\b \cf9 \strokec9 _resolve_now
\f1\b0 \cf5 \strokec5 (now_utc: \cf8 \strokec8 str\cf5 \strokec5  | 
\f0\b \cf2 \strokec2 None
\f1\b0 \cf5 \strokec5 ) -> datetime:\
    
\f0\b \cf2 \strokec2 if
\f1\b0 \cf5 \strokec5  
\f0\b \cf5 \strokec10 not
\f1\b0 \cf5 \strokec5  now_utc:\
        
\f0\b \cf2 \strokec2 return
\f1\b0 \cf5 \strokec5  datetime.now(timezone.utc)\
    
\f0\b \cf2 \strokec2 try
\f1\b0 \cf5 \strokec5 :\
        dt = datetime.fromisoformat(now_utc)\
        
\f0\b \cf2 \strokec2 if
\f1\b0 \cf5 \strokec5  dt.tzinfo 
\f0\b \cf5 \strokec10 is
\f1\b0 \cf5 \strokec5  
\f0\b \cf2 \strokec2 None
\f1\b0 \cf5 \strokec5 :\
            dt = dt.replace(tzinfo=timezone.utc)\
        
\f0\b \cf2 \strokec2 return
\f1\b0 \cf5 \strokec5  dt.astimezone(timezone.utc)\
    
\f0\b \cf2 \strokec2 except
\f1\b0 \cf5 \strokec5  
\f0\b \cf11 \strokec11 ValueError
\f1\b0 \cf5 \strokec5  
\f0\b \cf2 \strokec2 as
\f1\b0 \cf5 \strokec5  exc:\
        
\f0\b \cf2 \strokec2 raise
\f1\b0 \cf5 \strokec5  HTTPException(status_code=
\f0\b \cf12 \strokec12 400
\f1\b0 \cf5 \strokec5 , detail=\cf5 \cb6 \strokec5 f"Invalid now_utc: \cb13 \{\cf5 \cb1 \strokec5 exc\cf5 \cb13 \strokec5 \}\cb6 "\cf5 \cb1 \strokec5 ) 
\f0\b \cf2 \strokec2 from
\f1\b0 \cf3 \strokec3  
\f0\b \cf4 \strokec4 exc
\f1\b0 \cf5 \strokec5 \
\
\
\pard\pardeftab720\partightenfactor0

\f0\b \cf14 \strokec14 @app
\f1\b0 \cf5 \strokec5 .get(\cf5 \cb6 \strokec5 "/health"\cf5 \cb1 \strokec5 )\
\pard\pardeftab720\partightenfactor0

\f0\b \cf2 \strokec2 def
\f1\b0 \cf3 \strokec3  
\f0\b \cf9 \strokec9 health
\f1\b0 \cf5 \strokec5 () -> Dict[\cf8 \strokec8 str\cf5 \strokec5 , \cf8 \strokec8 str\cf5 \strokec5 ]:\
    
\f0\b \cf2 \strokec2 return
\f1\b0 \cf5 \strokec5  \{\cf5 \cb6 \strokec5 "status"\cf5 \cb1 \strokec5 : \cf5 \cb6 \strokec5 "ok"\cf5 \cb1 \strokec5 \}\
\
\
\pard\pardeftab720\partightenfactor0

\f0\b \cf14 \strokec14 @app
\f1\b0 \cf5 \strokec5 .post(\cf5 \cb6 \strokec5 "/analyze"\cf5 \cb1 \strokec5 , response_model=AnalyzeResponse)\
\pard\pardeftab720\partightenfactor0

\f0\b \cf2 \strokec2 def
\f1\b0 \cf3 \strokec3  
\f0\b \cf9 \strokec9 analyze
\f1\b0 \cf5 \strokec5 (payload: AnalyzeRequest) -> AnalyzeResponse:\
    now = _resolve_now(payload.now_utc)\
    routed = route_request(\
        account_id=payload.account_id,\
        query=payload.query,\
        now=now,\
    )\
    
\f0\b \cf2 \strokec2 return
\f1\b0 \cf5 \strokec5  AnalyzeResponse(**routed)\
}