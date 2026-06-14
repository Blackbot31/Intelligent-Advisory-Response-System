import hashlib
import hmac
import secrets
import uuid
from datetime import datetime
from cryptography.fernet import Fernet


class SecuredResourceRepository:
    def __init__(self):
        self.encryption_key = Fernet.generate_key()
        self.cipher         = Fernet(self.encryption_key)
        self.users          = {}
        self.resources      = {}
        self.access_log     = []
        self.sessions       = {}

        self.access_levels = {
            "admin":   ["read", "write", "delete", "manage_users"],
            "officer": ["read", "write"],
            "viewer":  ["read"],
            "analyst": ["read", "write"]
        }

        self.nlp_commands = {
            "show resources":   "list_resources",
            "list resources":   "list_resources",
            "view resources":   "list_resources",
            "add resource":     "add_resource",
            "store resource":   "add_resource",
            "search":           "search_resource",
            "find":             "search_resource",
            "access log":       "view_access_log",
            "show log":         "view_access_log",
            "view log":         "view_access_log",
            "help":             "show_help",
            "show help":        "show_help",
            "what can i do":    "show_help",
            "consult":          "remote_consultation",
            "consultation":     "remote_consultation",
            "ask":              "remote_consultation",
            "advise":           "remote_consultation",
            "what should i do": "remote_consultation",
            "how do i":         "remote_consultation",
            "how should i":     "remote_consultation",
            "what is":          "remote_consultation",
            "what are":         "remote_consultation",
            "explain":          "remote_consultation",
            "recommend":        "remote_consultation",
            "what ppe":             "remote_consultation",
            "ppe for":              "remote_consultation",
            "how to manage":        "remote_consultation",
            "how to handle":        "remote_consultation",
            "how to set up":        "remote_consultation",
            "tell me about":        "remote_consultation",
            "give me advice":       "remote_consultation",
            "what do i do":         "remote_consultation",
            "steps for":            "remote_consultation",
            "protocol for":         "remote_consultation",
            "cholera":          "remote_consultation",
            "mpox":             "remote_consultation",
            "ebola":            "remote_consultation",
            "covid":            "remote_consultation",
            "isolation":        "remote_consultation",
            "contact tracing":  "remote_consultation",
            "surveillance":     "remote_consultation",
            "resource":         "remote_consultation",
        }

    def hash_password(self, password):
        salt   = secrets.token_hex(16)
        hashed = hmac.new(
            salt.encode(), password.encode(), hashlib.sha256
        ).hexdigest()
        return f"{salt}:{hashed}"

    def verify_password(self, password, stored_hash):
        salt, hashed = stored_hash.split(":")
        check = hmac.new(
            salt.encode(), password.encode(), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(hashed, check)

    def register_user(self, username, password, role):
        if username in self.users:
            return {"error": "User already exists"}
        if role not in self.access_levels:
            return {"error": "Invalid role"}
        user_id = str(uuid.uuid4())[:8].upper()
        self.users[username] = {
            "user_id":        user_id,
            "username":       username,
            "password_hash":  self.hash_password(password),
            "role":           role,
            "permissions":    self.access_levels[role],
            "date_registered": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return {"success": True, "user_id": user_id, "role": role}

    def login(self, username, password):
        if username not in self.users:
            return {"error": "Invalid credentials"}
        user = self.users[username]
        if not self.verify_password(password, user["password_hash"]):
            return {"error": "Invalid credentials"}
        session_token = secrets.token_hex(32)
        self.sessions[session_token] = {
            "username":    username,
            "role":        user["role"],
            "permissions": user["permissions"],
            "login_time":  datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return {
            "success":       True,
            "session_token": session_token,
            "role":          user["role"],
            "permissions":   user["permissions"]
        }

    def verify_session(self, session_token):
        return self.sessions.get(session_token)

    def encrypt_data(self, data):
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt_data(self, encrypted_data):
        return self.cipher.decrypt(encrypted_data.encode()).decode()

    def store_resource(self, session_token, resource_name,
                       resource_data, classification):
        session = self.verify_session(session_token)
        if not session:
            return {"error": "Unauthorised access"}
        if "write" not in session["permissions"]:
            return {"error": "Insufficient permissions"}
        resource_id = str(uuid.uuid4())[:8].upper()
        encrypted   = self.encrypt_data(str(resource_data))
        self.resources[resource_id] = {
            "resource_id":   resource_id,
            "name":          resource_name,
            "classification": classification,
            "encrypted_data": encrypted,
            "stored_by":     session["username"],
            "date_stored":   datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.log_access(session["username"], "WRITE",
                        resource_id, "Resource stored successfully")
        return {"success": True, "resource_id": resource_id,
                "classification": classification}

    def retrieve_resource(self, session_token, resource_id):
        session = self.verify_session(session_token)
        if not session:
            return {"error": "Unauthorised access"}
        if "read" not in session["permissions"]:
            return {"error": "Insufficient permissions"}
        if resource_id not in self.resources:
            return {"error": "Resource not found"}
        resource  = self.resources[resource_id]
        decrypted = self.decrypt_data(resource["encrypted_data"])
        self.log_access(session["username"], "READ",
                        resource_id, "Resource retrieved successfully")
        return {
            "resource_id":    resource_id,
            "name":           resource["name"],
            "classification": resource["classification"],
            "data":           decrypted,
            "stored_by":      resource["stored_by"],
            "date_stored":    resource["date_stored"]
        }

    def log_access(self, username, action, resource_id, note):
        self.access_log.append({
            "log_id":      str(uuid.uuid4())[:8].upper(),
            "username":    username,
            "action":      action,
            "resource_id": resource_id,
            "note":        note,
            "timestamp":   datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    def process_nlp_command(self, session_token, command):
        session = self.verify_session(session_token)
        if not session:
            return {"error": "Unauthorised access"}

        command_lower  = command.lower().strip()
        matched_action = None

        # Sort by phrase length descending so longer phrases match first
        sorted_commands = sorted(
            self.nlp_commands.items(),
            key=lambda x: len(x[0]),
            reverse=True
        )
        for phrase, action in sorted_commands:
            if phrase in command_lower:
                matched_action = action
                break

        if not matched_action:
            return {
                "response": "Command not recognised. Type 'help' "
                            "to see available commands."
            }

        if matched_action == "list_resources":
            return {
                "response":  "Available resources",
                "total":     len(self.resources),
                "resources": [
                    {
                        "id":             r["resource_id"],
                        "name":           r["name"],
                        "classification": r["classification"],
                        "stored_by":      r["stored_by"]
                    }
                    for r in self.resources.values()
                ]
            }

        elif matched_action == "view_access_log":
            return {
                "response":      "Access log retrieved",
                "total_entries": len(self.access_log),
                "log":           self.access_log[-5:]
            }

        elif matched_action == "show_help":
            return {
                "response": "Available commands",
                "commands": [
                    "show resources",
                    "view log",
                    "access log",
                    "help",
                    "consult [topic]",
                    "how do i [topic]",
                    "what should i do [topic]",
                    "explain [topic]",
                ],
                "consultation_topics": [
                    "cholera", "mpox", "ebola", "covid",
                    "isolation", "contact tracing",
                    "ppe", "surveillance", "resource"
                ]
    }

        elif matched_action == "remote_consultation":
            return self.handle_remote_consultation(command_lower)

        else:
            return {
                "response": f"Action '{matched_action}' "
                            f"requires additional parameters."
            }

    def handle_remote_consultation(self, query: str) -> dict:
        query_lower = query.lower()

        consultation_kb = {
            "cholera": {
                "condition": "Cholera",
                "immediate_actions": [
                    "Isolate suspected cases immediately",
                    "Ensure access to oral rehydration salts (ORS)",
                    "Set up cholera treatment units in affected areas",
                    "Conduct rapid water and sanitation assessment",
                    "Alert national disease surveillance systems"
                ],
                "ppe_required": ["Gloves", "Gown", "Mask", "Boots"],
                "key_message": (
                    "Cholera spreads through contaminated water and food. "
                    "Immediate rehydration and water sanitation are critical."
                )
            },
            "mpox": {
                "condition": "Mpox",
                "immediate_actions": [
                    "Isolate confirmed and suspected cases",
                    "Conduct contact tracing of all exposed individuals",
                    "Deploy vaccination teams to high-risk zones",
                    "Issue community awareness advisories",
                    "Report to national surveillance system within 24 hours"
                ],
                "ppe_required": [
                    "Gloves", "Gown", "N95 Mask",
                    "Eye Protection", "Boots"
                ],
                "key_message": (
                    "Mpox spreads through close physical contact. "
                    "Isolation and contact tracing are the primary "
                    "response measures."
                )
            },
            "ebola": {
                "condition": "Ebola Virus Disease",
                "immediate_actions": [
                    "Immediately activate national emergency response",
                    "Establish Ebola Treatment Units with full barrier nursing",
                    "Deploy trained rapid response teams",
                    "Conduct aggressive contact tracing",
                    "Request international technical support"
                ],
                "ppe_required": [
                    "Full body suit", "Double gloves", "N95 Mask",
                    "Face shield", "Boots", "Apron"
                ],
                "key_message": (
                    "Ebola is highly lethal. Strict infection prevention "
                    "and control measures must be enforced at all times."
                )
            },
            "covid": {
                "condition": "COVID-19",
                "immediate_actions": [
                    "Activate case isolation and quarantine protocols",
                    "Scale up testing and contact tracing",
                    "Enforce respiratory hygiene and mask use",
                    "Assess healthcare facility capacity",
                    "Communicate risk to the public clearly"
                ],
                "ppe_required": [
                    "Surgical Mask", "Gloves", "Gown", "Eye Protection"
                ],
                "key_message": (
                    "COVID-19 spreads through respiratory droplets. "
                    "Vaccination, masking, and ventilation are key "
                    "preventive measures."
                )
            },
            "isolation": {
                "condition": "Isolation Centre Setup",
                "immediate_actions": [
                    "Select a location separate from the main health facility",
                    "Ensure dedicated staff assigned only to isolation area",
                    "Establish clear entry and exit protocols",
                    "Provide adequate PPE stocks for all staff",
                    "Set up hand hygiene stations at all entry points",
                    "Ensure proper waste management and disposal"
                ],
                "ppe_required": [
                    "Gloves", "Gown", "Mask", "Eye Protection"
                ],
                "key_message": (
                    "An effective isolation centre requires clear patient "
                    "flow, dedicated staff, adequate PPE, and strict "
                    "infection prevention protocols."
                )
            },
            "contact tracing": {
                "condition": "Contact Tracing Protocol",
                "immediate_actions": [
                    "Identify all contacts within the defined exposure window",
                    "Register all contacts in a monitoring database",
                    "Conduct daily follow-up with all contacts",
                    "Provide contacts with clear guidance on symptoms to watch for",
                    "Arrange rapid testing for contacts showing symptoms",
                    "Escalate immediately if a contact develops symptoms"
                ],
                "ppe_required": ["Mask", "Gloves"],
                "key_message": (
                    "Effective contact tracing must begin within 24 hours "
                    "of case identification. Speed and completeness are critical."
                )
            },
            "ppe": {
                "condition": "Personal Protective Equipment (PPE)",
                "immediate_actions": [
                    "Conduct immediate PPE stock assessment",
                    "Prioritise distribution to frontline health workers",
                    "Train all staff on correct donning and doffing procedures",
                    "Establish PPE restock request procedures",
                    "Monitor daily PPE consumption rates"
                ],
                "ppe_required": [
                    "Varies by disease — see specific disease protocols"
                ],
                "key_message": (
                    "PPE is only effective when used correctly and consistently. "
                    "Training on proper use is as important as the supply itself."
                )
            },
            "surveillance": {
                "condition": "Disease Surveillance",
                "immediate_actions": [
                    "Activate enhanced surveillance at all health facilities",
                    "Ensure immediate case reporting to district and national levels",
                    "Conduct active case search in affected communities",
                    "Set up sentinel surveillance sites if not already in place",
                    "Review and update case definitions for the disease"
                ],
                "ppe_required": ["Mask", "Gloves"],
                "key_message": (
                    "Early detection through strong surveillance systems "
                    "is the foundation of effective outbreak response."
                )
            },
            "resource": {
                "condition": "Resource Management During Outbreaks",
                "immediate_actions": [
                    "Conduct immediate needs assessment in all affected areas",
                    "Prioritise resource deployment based on disease burden",
                    "Establish a central resource coordination point",
                    "Track all resource movements with unique identifiers",
                    "Report resource gaps immediately to coordination authority"
                ],
                "ppe_required": ["N/A"],
                "key_message": (
                    "Transparent and data-driven resource management "
                    "is essential for equitable and effective outbreak response."
                )
            }
        }

        matched_topic = None
        for keyword, data in consultation_kb.items():
            if keyword in query_lower:
                matched_topic = data
                break

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if matched_topic:
            lines = []
            lines.append("IARMS REMOTE HEALTH CONSULTATION")
            lines.append(f"Timestamp: {timestamp}")
            lines.append(f"Query: {query}")
            lines.append("")
            lines.append(f"CONDITION: {matched_topic['condition']}")
            lines.append("")
            lines.append("RECOMMENDED IMMEDIATE ACTIONS:")
            for i, action in enumerate(matched_topic["immediate_actions"], 1):
                lines.append(f"  {i}. {action}")
            lines.append("")
            lines.append("PPE REQUIREMENTS:")
            for item in matched_topic["ppe_required"]:
                lines.append(f"  - {item}")
            lines.append("")
            lines.append("KEY MESSAGE:")
            lines.append(f"  {matched_topic['key_message']}")
            lines.append("")
            lines.append(
                "Note: This consultation is generated by the IARMS knowledge "
                "base. Always verify guidance with your national health "
                "authority and current WHO protocols."
            )
            return {
                "type":     "consultation",
                "response": "\n".join(lines),
                "topic":    matched_topic["condition"]
            }
        else:
            general_topics = list(consultation_kb.keys())
            return {
                "type": "consultation",
                "response": (
                    f"IARMS REMOTE HEALTH CONSULTATION\n"
                    f"Timestamp: {timestamp}\n"
                    f"Query: {query}\n\n"
                    f"Your query did not match a specific topic in the "
                    f"consultation knowledge base.\n\n"
                    f"Available consultation topics:\n" +
                    "\n".join(
                        f"  - {t.title()}" for t in general_topics
                    ) +
                    f"\n\nTry asking about one of these topics or use "
                    f"keywords such as the disease name, 'isolation', "
                    f"'contact tracing', 'PPE', 'surveillance', or 'resource'."
                ),
                "topic": "General"
            }


# ── Quick Test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    srr = SecuredResourceRepository()
    srr.register_user("admin_user", "SecurePass123", "admin")
    session = srr.login("admin_user", "SecurePass123")
    token   = session["session_token"]

    result = srr.process_nlp_command(
        token, "what should i do for cholera outbreak"
    )
    print(result["response"])
    print("\nSRR subsystem loaded successfully!")