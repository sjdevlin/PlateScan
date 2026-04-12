from sqlalchemy import Column, Float, Integer, String

from .base import Base


class Plate(Base):
    __tablename__ = "Plate"

    id = Column(Integer, primary_key=True)
    description = Column(String)
    opentrons_name = Column(String)
    outline_width = Column(Float)
    outline_length = Column(Float)
    outline_height = Column(Float)
    num_rows = Column(Integer)
    num_cols = Column(Integer)
    centre_first_well_offset_x = Column(Float)
    centre_first_well_offset_y = Column(Float)
    well_type = Column(String)
    well_dimension = Column(Float)
    well_depth = Column(Float)
    well_spacing_x = Column(Float)
    well_spacing_y = Column(Float)
    min_well_volume = Column(Float)
    max_well_volume = Column(Float)
