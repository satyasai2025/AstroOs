from dataclasses import dataclass

@dataclass
class JobRequest:
    task_type: str
    payload: dict

# Add additional fields as needed