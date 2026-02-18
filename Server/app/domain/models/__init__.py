from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.domain.models.startup import Startup  # noqa: E402, F401
from app.domain.models.monthly_indicator import MonthlyIndicator  # noqa: E402, F401
from app.domain.models.board_meeting import BoardMeeting  # noqa: E402, F401
from app.domain.models.executive import Executive  # noqa: E402, F401
from app.domain.models.deal import Deal  # noqa: E402, F401
from app.domain.models.report_token import ReportToken  # noqa: E402, F401
