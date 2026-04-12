from sqlalchemy import create_engine
from sqlalchemy.orm import joinedload, sessionmaker

from models import Base, Image, ImageSet, Plate, ResultRun


DEFAULT_PLATES = [
    {
        "description": "36 Well Integrated Plate",
        "opentrons_name": "",
        "outline_width": 127.8,
        "outline_length": 85.5,
        "outline_height": 15.5,
        "num_rows": 6,
        "num_cols": 6,
        "centre_first_well_offset_x": 19.0,
        "centre_first_well_offset_y": 11.5,
        "well_type": "circular",
        "well_dimension": 1.5,
        "well_depth": 13.0,
        "well_spacing_x": 12.5,
        "well_spacing_y": 12.5,
        "min_well_volume": 10.0,
        "max_well_volume": 50.0,
    },
    {
        "description": "Ibidi 96 Square Well Glass",
        "opentrons_name": "",
        "outline_width": 127.8,
        "outline_length": 85.5,
        "outline_height": 15.0,
        "num_rows": 8,
        "num_cols": 12,
        "centre_first_well_offset_x": 14.5,
        "centre_first_well_offset_y": 11.3,
        "well_type": "Square",
        "well_dimension": 7.4,
        "well_depth": 13.0,
        "well_spacing_x": 9.0,
        "well_spacing_y": 9.0,
        "min_well_volume": 50.0,
        "max_well_volume": 200.0,
    },
    {
        "description": "24 Well Integrated Annealer",
        "opentrons_name": "",
        "outline_width": 127.8,
        "outline_length": 85.5,
        "outline_height": 16.0,
        "num_rows": 4,
        "num_cols": 6,
        "centre_first_well_offset_x": 16.0,
        "centre_first_well_offset_y": 18.75,
        "well_type": "circular",
        "well_dimension": 2.0,
        "well_depth": 15.0,
        "well_spacing_x": 16.0,
        "well_spacing_y": 16.0,
        "min_well_volume": 50.0,
        "max_well_volume": 100.0,
    },
]


class DatabaseService:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)
        self._seed_default_plates_if_needed()

    def _seed_default_plates_if_needed(self):
        with self.Session() as session:
            existing_count = session.query(Plate).count()
            if existing_count > 0:
                return

            for plate_data in DEFAULT_PLATES:
                session.add(Plate(**plate_data))
            session.commit()

    # Plates
    def get_all_plates(self):
        with self.Session() as session:
            return session.query(Plate).order_by(Plate.id).all()

    def get_plate_by_id(self, plate_id):
        with self.Session() as session:
            return session.query(Plate).filter_by(id=plate_id).first()

    def add_plate(self, plate):
        with self.Session() as session:
            session.add(plate)
            session.commit()
            return plate.id

    # Image sets
    def get_image_set_by_id(self, image_set_id):
        with self.Session() as session:
            return session.query(ImageSet).filter_by(id=image_set_id).first()

    def get_all_image_sets(self):
        with self.Session() as session:
            return session.query(ImageSet).order_by(ImageSet.id).all()

    def add_image_set(self, image_set):
        with self.Session() as session:
            session.add(image_set)
            session.commit()
            return image_set.id

    def update_image_set(self, image_set):
        with self.Session() as session:
            session.merge(image_set)
            session.commit()
            return True

    def count_result_runs_for_image_set(self, image_set_id):
        with self.Session() as session:
            return session.query(ResultRun).filter_by(image_set_id=image_set_id).count()

    def delete_image_set(self, image_set_id):
        with self.Session() as session:
            image_set = session.query(ImageSet).filter_by(id=image_set_id).first()
            if image_set is None:
                return False
            session.delete(image_set)
            session.commit()
            return True

    # Result runs
    def add_result_run(self, result_run):
        with self.Session() as session:
            session.add(result_run)
            session.commit()
            return result_run.id

    def get_result_run_by_id(self, result_run_id):
        with self.Session() as session:
            return session.query(ResultRun).filter_by(id=result_run_id).first()

    def get_all_result_runs(self):
        with self.Session() as session:
            return session.query(ResultRun).options(joinedload(ResultRun.image)).order_by(ResultRun.id.desc()).all()

    def update_result_run(self, result_run):
        with self.Session() as session:
            session.merge(result_run)
            session.commit()
            return True

    def delete_result_run(self, result_run_id):
        with self.Session() as session:
            result_run = session.query(ResultRun).filter_by(id=result_run_id).first()
            if result_run is None:
                return False
            session.delete(result_run)
            session.commit()
            return True

    # Images
    def add_result_run_image(self, image):
        with self.Session() as session:
            session.add(image)
            session.commit()
            return image.id

    def get_images_by_result_run_id(self, result_run_id):
        with self.Session() as session:
            return session.query(Image).filter_by(result_run_id=result_run_id).order_by(Image.id).all()
