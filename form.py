import re
import pandas as pd


class Form:
    def __init__(self, file_path):
        self.file_path = file_path

    def process_conditions_section(self):
        with open(self.file_path, "r") as file:
            text = file.read()

        # Extract the CONDITIONS section
        conditions_section = re.search(
            r"CONDITIONS:\n(.*?)\n-{80}", text, re.DOTALL
        ).group(1)

        # Split the section into individual condition entries
        condition_entries = conditions_section.strip().split("\n")

        # Initialize lists to store the parsed data
        start_dates = []
        end_dates = []
        descriptions = []
        types = []

        # Parse each condition entry
        for entry in condition_entries:
            match = re.match(
                r"\s*(\d{4}-\d{2}-\d{2}) -\s*(\d{4}-\d{2}-\d{2}|)\s*:\s*(.*?)\s*\((.*?)\)",
                entry,
            )
            if match:
                start_date = match.group(1)
                end_date = match.group(2) if match.group(2) else None
                description = match.group(3)
                type_ = match.group(4)

                start_dates.append(start_date)
                end_dates.append(end_date)
                descriptions.append(description)
                types.append(type_)

        # Create a DataFrame from the parsed data
        df = pd.DataFrame(
            {
                "start": start_dates,
                "end": end_dates,
                "description": descriptions,
                "type": types,
            }
        )

        return df

    def process_observations_section(self):
        # Read the text file
        with open(self.file_path, "r") as file:
            text = file.read()

        # Extract the observations section
        observations_section = re.search(
            r"OBSERVATIONS:(.*?)(?=IMMUNIZATIONS:)", text, re.DOTALL
        ).group(1)

        # Split the observations into individual entries
        observations = re.findall(
            r"(\d{4}-\d{2}-\d{2}.*?)(?=\d{4}-\d{2}-\d{2}|$)",
            observations_section,
            re.DOTALL,
        )

        # Create a DataFrame with columns date and content
        data = []
        for observation in observations:
            date = re.search(r"\d{4}-\d{2}-\d{2}", observation).group(0)
            content = observation[len(date) :].strip()
            if content.startswith(":"):
                content = content[1:].strip()
            data.append([date, content])

        df = pd.DataFrame(data, columns=["date", "content"])

        return df

    def process_medications_section(self):
        # Read the text file
        with open(self.file_path, "r") as file:
            text = file.read()

        # Extract the MEDICATIONS section
        medications_section = re.search(
            r"MEDICATIONS:\n(.*?)\n-{80}", text, re.DOTALL
        ).group(1)

        # Split the section into individual medication entries
        medication_entries = medications_section.strip().split("\n")

        # Initialize lists to store the parsed data
        dates = []
        statuses = []
        medications = []
        reasons = []
        types = []

        # Parse each medication entry
        for entry in medication_entries:
            match = re.match(
                r"\s*(\d{4}-\d{2}-\d{2})\[(CURRENT|STOPPED)\]\s*:\s*(.*?)\s*for\s*(.*)\s*\((.*?)\)",
                entry,
            )
            if match:
                date = match.group(1)
                status = match.group(2)
                medication = match.group(3)
                reason = match.group(4)
                type_ = match.group(5)

                dates.append(date)
                statuses.append(status)
                medications.append(medication)
                reasons.append(reason)
                types.append(type_)

        # Create a DataFrame from the parsed data
        df = pd.DataFrame(
            {
                "date": dates,
                "status": statuses,
                "medication": medications,
                "reason": reasons,
                "type": types,
            }
        )

        return df

    def print_form(self):
        """
        Prints the form to stdout in a streamed manner to avoid loading the entire file into memory.
        """
        with open(self.file_path, "r") as file:
            for line in file:
                print(line, end="")
