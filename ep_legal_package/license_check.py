{\rtf1\ansi\ansicpg1252\cocoartf2759
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fmodern\fcharset0 Courier-Bold;\f1\fmodern\fcharset0 Courier;}
{\colortbl;\red255\green255\blue255;\red16\green121\blue2;\red173\green173\blue173;\red19\green112\blue166;
\red38\green38\blue38;\red67\green67\blue67;\red170\green0\blue83;\red12\green95\blue24;\red117\green117\blue117;
\red255\green236\blue236;\red9\green80\blue173;\red0\green0\blue0;}
{\*\expandedcolortbl;;\cssrgb\c0\c53333\c0;\cssrgb\c73333\c73333\c73333;\cssrgb\c5490\c51765\c70980;
\cssrgb\c20000\c20000\c20000;\cssrgb\c33333\c33333\c33333;\cssrgb\c73333\c0\c40000;\cssrgb\c0\c43922\c12549;\cssrgb\c53333\c53333\c53333;
\cssrgb\c100000\c94118\c94118;\cssrgb\c0\c40000\c73333;\cssrgb\c0\c0\c0;}
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
\f1\b0 \cf5 \strokec5  Dict\
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
\pard\pardeftab720\partightenfactor0
\cf9 \strokec9 # Demo in-memory license table.\cf5 \strokec5 \
\cf9 \strokec9 # Replace with database or signed token validation in production.\cf5 \strokec5 \
LICENSE_TABLE: Dict[\cf8 \strokec8 str\cf5 \strokec5 , \cf8 \strokec8 str\cf5 \strokec5 ] = \{\
    \cf5 \cb10 \strokec5 "demo_account_1"\cf5 \cb1 \strokec5 : \cf5 \cb10 \strokec5 "2026-12-31T23:59:59+00:00"\cf5 \cb1 \strokec5 ,\
    \cf5 \cb10 \strokec5 "partner_account_alpha"\cf5 \cb1 \strokec5 : \cf5 \cb10 \strokec5 "2026-06-30T23:59:59+00:00"\cf5 \cb1 \strokec5 ,\
    \cf5 \cb10 \strokec5 "wesley_admin"\cf5 \cb1 \strokec5 : \cf5 \cb10 \strokec5 "2099-12-31T23:59:59+00:00"\cf5 \cb1 \strokec5 ,\
\}\
\
\
\pard\pardeftab720\partightenfactor0

\f0\b \cf2 \strokec2 def
\f1\b0 \cf3 \strokec3  
\f0\b \cf11 \strokec11 _parse_iso_datetime
\f1\b0 \cf5 \strokec5 (value: \cf8 \strokec8 str\cf5 \strokec5 ) -> datetime:\
    dt = datetime.fromisoformat(value)\
    
\f0\b \cf2 \strokec2 if
\f1\b0 \cf5 \strokec5  dt.tzinfo 
\f0\b \cf5 \strokec12 is
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
\f0\b \cf5 \strokec12 not
\f1\b0 \cf5 \strokec5  
\f0\b \cf5 \strokec12 in
\f1\b0 \cf5 \strokec5  LICENSE_TABLE:\
        
\f0\b \cf2 \strokec2 return
\f1\b0 \cf5 \strokec5  LicenseStatus(\
            account_id=account_id,\
            authorized=
\f0\b \cf2 \strokec2 False
\f1\b0 \cf5 \strokec5 ,\
            reason=\cf5 \cb10 \strokec5 "account_not_authorized"\cf5 \cb1 \strokec5 ,\
            valid_until=
\f0\b \cf2 \strokec2 None
\f1\b0 \cf5 \strokec5 ,\
        )\
\
    valid_until = _parse_iso_datetime(LICENSE_TABLE[account_id])\
\
    
\f0\b \cf2 \strokec2 if
\f1\b0 \cf5 \strokec5  now.astimezone(timezone.utc) > valid_until:\
        
\f0\b \cf2 \strokec2 return
\f1\b0 \cf5 \strokec5  LicenseStatus(\
            account_id=account_id,\
            authorized=
\f0\b \cf2 \strokec2 False
\f1\b0 \cf5 \strokec5 ,\
            reason=\cf5 \cb10 \strokec5 "license_expired"\cf5 \cb1 \strokec5 ,\
            valid_until=valid_until,\
        )\
\
    
\f0\b \cf2 \strokec2 return
\f1\b0 \cf5 \strokec5  LicenseStatus(\
        account_id=account_id,\
        authorized=
\f0\b \cf2 \strokec2 True
\f1\b0 \cf5 \strokec5 ,\
        reason=\cf5 \cb10 \strokec5 "authorized"\cf5 \cb1 \strokec5 ,\
        valid_until=valid_until,\
    )\
}