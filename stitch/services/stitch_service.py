from stitch.models.stitch import Stitch, get_stitches

class StitchService:
    """Manage stitch operations"""

    @staticmethod
    def get_all_stitches() -> list[dict]:
        """
        Get all available stitch types.

        Returns:
            List of dictionaries representing stitch types
        """
        stitches = get_stitches()
        return [stitch.to_dict() for stitch in stitches]