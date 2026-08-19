import datetime
def get_datetime():
    dt1 = datetime.datetime.now()
    print(dt1)
    return dt1.strftime("%d %B, %Y")
monthstr = get_datetime()
print(monthstr)
urlapi= '/stockurl'
ERRORNOTIFICATIONARN = '/data/errorarn'
SUCCESSNOTIFICATIONARN='/data/successarn'
COMPONENT_NAME = 'DL_DATA_REPO_EXTRACT'
# ERROR_MSG = f'NEED ATTENTION ****API ERROR /KEY EXPIRED ** ON {monthstr} ******'
ERROR_MSG = f'NEED ATTENTION ****URL GOT CHANGED  ** ON {monthstr} ******'
SUCCESS_MSG = f'SUCCESSFULLY EXTRACTED  FILES FOR {monthstr}*'
SUCCESS_DESCRIPTION='SUCCESS'
ENVIRONMENT = '/data/env'