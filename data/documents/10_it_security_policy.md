# IT Security Policy for ChandraAILabs

---

**Document Title:** ChandraAILabs IT Security Policy
**Version:** 1.0
**Effective Date:** October 26, 2023
**Last Updated:** October 26, 2023
**Approved By:** [ChandraAILabs Leadership/CISO]

---

## 1. Introduction

ChandraAILabs, an AI/ML product company, recognizes that information and intellectual property are among its most valuable assets. This IT Security Policy outlines the principles, responsibilities, and mandatory requirements to protect these assets from unauthorized access, use, disclosure, disruption, modification, or destruction.

The integrity, confidentiality, and availability of our systems, data, and proprietary AI models are paramount to maintaining customer trust, ensuring business continuity, and complying with applicable laws and regulations in India and globally.

All employees, contractors, interns, and third-party vendors working with ChandraAILabs are required to adhere to this policy.

## 2. Purpose

The purpose of this policy is to:
*   Safeguard ChandraAILabs' information assets, including proprietary AI models, algorithms, training data, customer data, and intellectual property.
*   Define clear security responsibilities for all personnel.
*   Mitigate risks associated with IT systems and data handling.
*   Ensure compliance with relevant legal, regulatory, and contractual obligations.
*   Promote a strong security culture within the organization.

## 3. Scope

This policy applies to all ChandraAILabs personnel (employees, contractors, interns), all company-owned or managed IT assets (hardware, software, networks, data centers, cloud infrastructure), and all information created, stored, processed, or transmitted by or on behalf of ChandraAILabs, regardless of its storage location. This includes both on-premises and cloud-based systems.

## 4. Definitions

*   **Company Assets:** All hardware, software, networks, data, intellectual property, and physical resources owned or used by ChandraAILabs.
*   **Confidential Data:** Information that, if disclosed, could cause significant harm to ChandraAILabs, its customers, or partners. This includes proprietary algorithms, source code, AI models, training data, and customer Personally Identifiable Information (PII).
*   **Employee:** Any full-time, part-time, temporary employee, contractor, intern, or consultant associated with ChandraAILabs.
*   **Incident:** Any event that could lead to a breach of security, compromise of data, or disruption of services.
*   **Intellectual Property (IP):** Proprietary information including algorithms, source code, AI model architectures, weights, training methodologies, and any other unique creations of ChandraAILabs.
*   **Least Privilege:** The principle that users should only be granted the minimum necessary access rights to perform their job functions.
*   **LLM:** Large Language Model, referring to AI models capable of processing and generating human-like text.
*   **Sensitive Data:** A broader category encompassing Confidential Data, customer data, financial information, HR data, and any other data requiring special protection.

## 5. General Security Principles

*   **Confidentiality:** Protect information from unauthorized disclosure.
*   **Integrity:** Ensure the accuracy, completeness, and reliability of information and processing methods.
*   **Availability:** Ensure authorized users have timely and reliable access to information and resources.
*   **Accountability:** All actions related to IT security are attributable to individuals.
*   **Least Privilege:** Access to information and systems will be granted on a "need-to-know" and "need-to-do" basis.
*   **Security by Design:** Security considerations will be integrated into the design and development of all systems, products, and processes from the outset.

## 6. Password Policy

Strong passwords are a primary defense against unauthorized access. All personnel must adhere to the following:

*   **Complexity:** Passwords must be at least 12 characters long and include a mix of uppercase letters, lowercase letters, numbers, and special characters.
*   **Uniqueness:** Passwords must not be reused across different systems or services, especially personal ones.
*   **MFA (Multi-Factor Authentication):** All critical systems, including but not limited to, company networks, cloud services, internal applications, and VPNs, must employ MFA.
*   **Confidentiality:** Passwords must never be written down, shared, or communicated verbally or electronically to anyone, including IT support.
*   **Storage:** Passwords must be stored securely in an approved password manager if necessary, but never on unprotected files or sticky notes.
*   **Change Frequency:** While not strictly enforced for strong, unique passwords with MFA, password resets will be triggered immediately upon suspicion of compromise.
*   **Account Lockout:** Systems will automatically lock out accounts after a specified number of failed login attempts.

## 7. Device Usage Policy

### 7.1. Company-Owned Devices

*   **Authorization:** Only company-issued and approved devices (laptops, desktops, mobile phones) may be used for company work.
*   **Security Software:** All devices must have mandatory security software (Antivirus/Anti-Malware, Endpoint Detection and Response - EDR) installed, kept up-to-date, and actively running.
*   **Encryption:** All company-issued laptops and mobile devices must have full disk encryption (FDE) enabled.
*   **Physical Security:** Devices must be physically secured at all times. Do not leave devices unattended in public places. Report lost or stolen devices immediately (refer to Incident Reporting).
*   **Software Installation:** Refer to Section 10 for software installation guidelines.
*   **Updates:** Operating systems and applications must be kept up-to-date with the latest security patches. Automatic updates are preferred where feasible.
*   **No Unauthorized Modifications:** Devices must not be rooted, jailbroken, or have any unauthorized modifications that could compromise their security.

### 7.2. Bring Your Own Device (BYOD) - (If Applicable, Otherwise State "Not Allowed")

*   **Note:** ChandraAILabs generally discourages BYOD for accessing sensitive company data due to inherent security risks. If BYOD is permitted for specific roles or scenarios, **it must be explicitly approved by IT management and adhere to stringent security measures, including:**
    *   Installation of company-managed security software.
    *   Enrollment in Mobile Device Management (MDM) for corporate data containers.
    *   Full disk encryption.
    *   Remote wipe capabilities (in case of loss/theft).
    *   Regular security patching and updates.
    *   Acceptable Use Policy compliance.
    *   Acknowledgement that the company may access corporate data on the device.

### 7.3. Remote Work & Network Usage

*   **VPN:** All connections to ChandraAILabs' internal networks and sensitive cloud resources must be made via an approved Virtual Private Network (VPN) solution.
*   **Secure Networks:** Employees working remotely must use secure, password-protected Wi-Fi networks. Avoid public Wi-Fi for sensitive work.
*   **Data Storage:** Sensitive company data must only be stored on approved company storage solutions (e.g., corporate cloud drives, secured network drives), not on personal cloud storage or local machine drives without proper encryption and sync.

## 8. Data Classification Policy

All data within ChandraAILabs is classified to ensure appropriate protection. Personnel are responsible for understanding and correctly classifying data they create, process, or store.

*   **8.1. Public Data:**
    *   **Definition:** Information intended for general public release, requiring no confidentiality.
    *   **Examples:** Public website content, marketing materials, job postings, public press releases.
    *   **Handling:** No specific security controls beyond general data management best practices.
*   **8.2. Internal Data:**
    *   **Definition:** Information not intended for public release, but generally not sensitive enough to cause significant harm if leaked.
    *   **Examples:** Internal memos, non-sensitive project plans, general internal communications.
    *   **Handling:** Accessible to all employees, but not to external parties without specific authorization.
*   **8.3. Confidential Data:**
    *   **Definition:** Information that, if disclosed, could cause moderate to significant harm to ChandraAILabs, its customers, or partners. Access is restricted to authorized personnel on a need-to-know basis.
    *   **Examples:** Customer non-PII project data, basic financial reports, HR records (non-medical), unreleased product specifications.
    *   **Handling:** Requires access controls, encryption at rest and in transit, and secure storage locations.
*   **8.4. Restricted Data (Highly Confidential):**
    *   **Definition:** Information whose unauthorized disclosure would cause severe harm, reputational damage, financial loss, or legal penalties. This includes all ChandraAILabs' Intellectual Property and sensitive customer data.
    *   **Examples:** Proprietary AI models (architectures, weights, parameters), source code, algorithms, training datasets containing PII or highly sensitive customer data, trade secrets, unpatented inventions, detailed financial projections, employee medical records.
    *   **Handling:** Requires the strictest controls:
        *   **Strict Access Control:** Granted only to specific individuals with explicit authorization and a demonstrable business need (least privilege principle).
        *   **Encryption:** Mandatory encryption at rest and in transit.
        *   **Auditing:** Regular logging and auditing of access attempts.
        *   **Secure Storage:** Stored only in designated, highly secured systems (e.g., dedicated secure cloud environments, encrypted databases).
        *   **Data Minimization:** Collect and retain only necessary restricted data.
        *   **Data Masking/Anonymization:** Implement where feasible for non-production environments.

## 9. AI Model Confidentiality Policy

ChandraAILabs' AI models, algorithms, and associated training data constitute its core Intellectual Property and are classified as **Restricted Data**.

*   **9.1. Protection of Models and Algorithms:**
    *   **Access Control:** Access to AI model repositories (e.g., codebases, model weights, deployment artifacts) is strictly controlled on a least-privilege basis.
    *   **Source Code Protection:** All model source code, algorithms, and development environments are treated as highly confidential. Version control systems must be secured.
    *   **Model Versioning & Audit Trails:** All changes to models and data should be logged and auditable.
    *   **Encryption:** Model files (weights, parameters) and deployment packages must be encrypted at rest and in transit.
    *   **No Unauthorized Exfiltration:** Exporting, downloading, or transferring models or training data outside of approved company systems is strictly prohibited.
    *   **Protection against Reverse Engineering:** While challenging, measures to deter unauthorized reverse engineering attempts (e.g., obfuscation, intellectual property clauses in contracts) will be considered and applied where appropriate.
    *   **API Key Management:** API keys for accessing internal or external AI services must be treated as highly confidential, rotated regularly, and never hardcoded into applications or public repositories.
*   **9.2. Training Data Confidentiality:**
    *   **Restricted Access:** Access to proprietary training datasets, especially those containing customer data or sensitive information, is severely restricted.
    *   **Data Minimization:** Only collect and use the minimum necessary data for training.
    *   **Anonymization/Pseudonymization:** Implement techniques to anonymize or pseudonymize sensitive data within training sets wherever possible.
    *   **Secure Storage:** Training data must be stored in designated, secured, and encrypted storage locations.
    *   **Data Retention:** Adhere to defined data retention policies for training data.
*   **9.3. Collaboration with Third Parties:**
    *   Any sharing of models, data, or algorithms with third parties (partners, customers, researchers) must be covered by Non-Disclosure Agreements (NDAs) and explicit contractual terms, reviewed by legal counsel.
    *   Access granted to third parties must be limited to the specific data or models required for their task and time-bound.

## 10. LLM Usage Policy (Large Language Model)

The use of LLMs (e.g., ChatGPT, Bard, Claude) can be beneficial but poses significant data leakage risks.

*   **10.1. Public/Unsanctioned LLMs (e.g., free public versions of ChatGPT, Bard):**
    *   **PROHIBITED for Sensitive Data:** Under no circumstances shall **Confidential** or **Restricted** data (including customer data, proprietary code, trade secrets, internal financial data, unreleased product features, AI model details) be inputted, pasted, or uploaded into public, unsanctioned LLMs.
    *   **General Use:** Public LLMs may be used for general research, generating generic text, brainstorming non-sensitive ideas, or summarization of publicly available information, provided no ChandraAILabs sensitive information is included in the prompts.
    *   **Disclaimer:** Users must be aware that any information submitted to public LLMs may be used by the LLM provider for training purposes and may lose its confidentiality.
*   **10.2. Approved Enterprise LLM Solutions:**
    *   ChandraAILabs may subscribe to enterprise-grade LLM solutions that offer data privacy, data retention policies, and robust security controls (e.g., dedicated instances, API access with specific data handling agreements).
    *   **Authorization:** Usage of such approved solutions will be communicated by the IT department, along with specific guidelines for their safe and ethical use.
    *   **Data Handling:** Even with approved enterprise LLMs, employees must exercise caution and adhere to the principle of least privilege regarding the data they input. Avoid oversharing.
*   **10.3. Internal LLM Deployments:**
    *   ChandraAILabs may develop or deploy its own internal LLM instances. These will be subject to the highest levels of security and confidentiality under the "AI Model Confidentiality Policy" (Section 9).
    *   **Guidelines:** Specific usage guidelines for internal LLMs will be provided by the development team.
*   **10.4. Responsibility:**
    *   Employees are personally responsible for any data leakage that occurs due to non-compliance with this LLM Usage Policy.
    *   Violation of this policy may lead to disciplinary action, up to and including termination of employment.

## 11. Software Installation Policy

*   **11.1. Authorized Software:**
    *   Only authorized and licensed software approved by the IT department may be installed on company-owned devices.
    *   A list of approved software will be maintained and communicated.
*   **11.2. Prohibited Software:**
    *   Installation of unauthorized personal software, shareware, freeware, peer-to-peer (P2P) file-sharing applications, or illegal software is strictly prohibited.
    *   Software that has not been scanned and approved by IT may introduce security vulnerabilities or malware.
*   **11.3. Installation Process:**
    *   All software installations (beyond standard OS/application updates) must be requested through the IT ticketing system and performed or approved by IT personnel.
    *   Developers requiring specific tools for their work must submit a request with justification to the IT department for review and approval.
*   **11.4. Licensing:**
    *   All software used on company devices must be properly licensed.

## 12. Incident Reporting Policy

Prompt reporting of security incidents is crucial for effective response and mitigation.

*   **12.1. What to Report:**
    *   Any suspected or actual security breach (e.g., unauthorized access, data leakage, malware infection).
    *   Loss or theft of company devices (laptops, mobile phones, USB drives).
    *   Suspicious emails (phishing attempts) or communications.
    *   Unusual system behavior or performance issues that might indicate a security compromise.
    *   Violation of this IT Security Policy.
*   **12.2. How to Report:**
    *   Immediately notify your direct manager and the IT Security Team.
    *   Report via [Specify Reporting Channel, e.g., security@chandraailabs.com or dedicated incident reporting portal].
    *   Provide as much detail as possible: what happened, when, where, and any relevant screenshots or logs.
*   **12.3. Timeliness:**
    *   All incidents, regardless of perceived severity, must be reported immediately upon discovery.
*   **12.4. Cooperation:**
    *   All personnel must fully cooperate with the IT Security Team during incident investigation and resolution.
    *   Do not attempt to fix the problem yourself unless explicitly instructed by the IT Security Team, as this might destroy critical forensic evidence.

## 13. Responsible AI Usage Policy

As an AI/ML company, ChandraAILabs is committed to developing and deploying AI responsibly and ethically.

*   **13.1. Fairness and Bias Mitigation:**
    *   Design, develop, and test AI models to identify and mitigate unfair biases that could lead to discriminatory outcomes.
    *   Ensure training data is diverse and representative where possible, and actively monitor for bias.
*   **13.2. Transparency and Explainability:**
    *   Strive for transparency in how AI systems operate, explaining their purpose, functionality, and limitations to stakeholders.
    *   Where feasible and necessary, incorporate explainability features to understand why an AI model made a particular decision.
*   **13.3. Accountability:**
    *   Clearly define roles and responsibilities for the development, deployment, and oversight of AI systems.
    *   Establish clear processes for addressing errors, biases, and adverse impacts of AI systems.
*   **13.4. Privacy by Design:**
    *   Integrate data privacy principles (e.g., data minimization, purpose limitation) into the design and development of AI systems from the outset.
    *   Ensure robust data protection measures are in place for all data used in AI development and operation, especially PII.
*   **13.5. Human Oversight:**
    *   Ensure that AI systems are designed to allow for meaningful human oversight and intervention, particularly in critical decision-making contexts.
*   **13.6. Safety and Robustness:**
    *   Develop and test AI systems for robustness against adversarial attacks and ensure they operate safely and reliably in intended environments.
*   **13.7. Legal and Regulatory Compliance:**
    *   Ensure all AI development and deployment comply with relevant laws and regulations, including data protection laws (e.g., GDPR, India's Personal Data Protection Bill when enacted), intellectual property laws, and emerging AI-specific regulations.
*   **13.8. Societal Impact Assessment:**
    *   Conduct assessments to understand and mitigate potential negative societal impacts of AI technologies developed by ChandraAILabs.

## 14. Training and Awareness

All personnel will undergo mandatory security awareness training upon joining ChandraAILabs and annually thereafter. This training will cover the principles outlined in this policy and best practices for information security.

## 15. Policy Review and Updates

This policy will be reviewed at least annually, or as needed, in response to changes in technology, business operations, legal/regulatory requirements, or identified risks. Any updates will be communicated to all personnel.

## 16. Enforcement and Disciplinary Action

Violation of this IT Security Policy can result in serious consequences, including:
*   Disciplinary action, up to and including termination of employment or contract.
*   Legal action and prosecution under applicable Indian and international laws.
*   Civil liability for damages.

ChandraAILabs reserves the right to monitor all company assets, networks, systems, and data to ensure compliance with this policy and for security purposes.

---

**Acknowledgement:**

I, [Employee Name], acknowledge that I have read, understood, and agree to comply with the ChandraAILabs IT Security Policy. I understand my responsibilities in protecting the company's information assets and that non-compliance may lead to disciplinary action.

**Employee Signature:** ____________________________
**Date:** ____________________________

---

**Disclaimer:** This policy is a living document and subject to change. It is not intended to be a legal document and does not constitute legal advice. For specific legal questions, please consult with legal counsel.