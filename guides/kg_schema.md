node_types = [
  {
    "NodeType": "AuditLog",
    "UniqueProperties": [
      "id",
      "user_id",
      "user_name",
      "resource_type",
      "resource_id",
      "action",
      "ip_address",
      "user_agent",
      "timestamp",
      "id",
      "user_id",
      "user_name",
      "resource_type",
      "resource_id",
      "action",
      "ip_address",
      "user_agent",
      "timestamp",
      "details"
    ]
  },
  {
    "NodeType": "File",
    "UniqueProperties": [
      "created_at",
      "id",
      "layman_summary",
      "file_status",
      "description",
      "file_size",
      "uploaded_by",
      "filename",
      "file_hash",
      "storage_path",
      "file_type",
      "category",
      "doctor_summary",
      "parsed_content"
    ]
  },
  {
    "NodeType": "HealthRecord",
    "UniqueProperties": [
      "updated_at",
      "created_at",
      "id",
      "ailment",
      "title",
      "created_by",
      "last_activity",
      "share_type",
      "share_token",
      "medications",
      "status",
      "layman_summary",
      "medical_summary",
      "overall_report"
    ]
  },
  {
    "NodeType": "Medication",
    "UniqueProperties": [
      "created_at",
      "id",
      "status",
      "end_date",
      "instructions",
      "dosage",
      "medication_name",
      "frequency",
      "side_effects",
      "prescribed_by",
      "duration_days",
      "start_date"
    ]
  },
  {
    "NodeType": "User",
    "UniqueProperties": [
      "user_type",
      "address",
      "updated_at",
      "gender",
      "phone",
      "date_of_birth",
      "name",
      "created_at",
      "id",
      "email",
      "user_type",
      "address",
      "updated_at",
      "gender",
      "phone",
      "date_of_birth",
      "name",
      "created_at",
      "id",
      "email",
      "specialization",
      "license_number"
    ]
  }
]

relationship_types = [
  {
    "Pattern": "HealthRecord -[HAS_FILE]-> File"
  },
  {
    "Pattern": "HealthRecord -[HAS_MEDICATION]-> Medication"
  },
  {
    "Pattern": "User -[MANAGES]-> HealthRecord"
  },
  {
    "Pattern": "User -[OWNS]-> HealthRecord"
  },
  {
    "Pattern": "User -[PRESCRIBED]-> Medication"
  },
  {
    "Pattern": "User -[TREATS]-> User"
  },
  {
    "Pattern": "User -[UPLOADED]-> File"
  }
]