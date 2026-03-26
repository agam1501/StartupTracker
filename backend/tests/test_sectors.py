from app.services.sectors import SECTORS, SECTORS_LIST, validate_sector


class TestSectors:
    def test_sectors_count(self):
        assert len(SECTORS) == 15

    def test_sectors_list_sorted(self):
        assert SECTORS_LIST == sorted(SECTORS_LIST)

    def test_validate_valid(self):
        assert validate_sector("AI/ML") == "AI/ML"
        assert validate_sector("Fintech") == "Fintech"
        assert validate_sector("Other") == "Other"

    def test_validate_case_insensitive(self):
        assert validate_sector("ai/ml") == "AI/ML"
        assert validate_sector("FINTECH") == "Fintech"
        assert validate_sector("cybersecurity") == "Cybersecurity"

    def test_validate_invalid(self):
        assert validate_sector("NotASector") is None
        assert validate_sector("") is None
        assert validate_sector(None) is None

    def test_known_sectors(self):
        expected = {
            "AI/ML",
            "Fintech",
            "Healthcare/Biotech",
            "SaaS/Enterprise",
            "E-Commerce/Retail",
            "Climate/Energy",
            "Cybersecurity",
            "EdTech",
            "Real Estate/PropTech",
            "Transportation/Logistics",
            "Media/Entertainment",
            "Food/Agriculture",
            "Hardware/Robotics",
            "Crypto/Web3",
            "Other",
        }
        assert SECTORS == expected
