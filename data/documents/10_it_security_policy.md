This IT Security Policy document outlines the mandatory requirements and guidelines for all employees, contractors, and third parties accessing TechCorp India's information systems and data. Its purpose is to protect the confidentiality, integrity, and availability of TechCorp's information assets.

---

# TechCorp India IT Security Policy

*Version: 1.0*
*Effective Date: 2023-10-27*
*Reviewed By: CISO & Legal Department*

## Table of Contents

1.  [Introduction](#1-introduction)
2.  [Policy Scope](#2-policy-scope)
3.  [Policy Objectives](#3-policy-objectives)
4.  [Roles and Responsibilities](#4-roles-and-responsibilities)
5.  [General Security Principles](#5-general-security-principles)
6.  [Password Policy](#6-password-policy)
7.  [Device Usage Policy](#7-device-usage-policy)
    *   [Company-Owned Devices](#71-company-owned-devices)
    *   [Bring Your Own Device (BYOD)](#72-bring-your-own-device-byod)
    *   [Physical Security of Devices](#73-physical-security-of-devices)
8.  [Data Classification Policy](#8-data-classification-policy)
    *   [Data Classification Levels](#81-data-classification-levels)
    *   [Data Handling Guidelines](#82-data-handling-guidelines)
9.  [Email Usage Policy](#9-email-usage-policy)
10. [Software Installation and Usage Policy](#10-software-installation-and-usage-policy)
11. [Incident Reporting and Response Policy](#11-incident-reporting-and-response-policy)
12. [Access Control Policy](#12-access-control-policy)
13. [Network Security Policy](#13-network-security-policy)
14. [Third-Party and Vendor Access Policy](#14-third-party-and-vendor-access-policy)
15. [Security Awareness and Training](#15-security-awareness-and-training)
16. [Compliance and Enforcement](#16-compliance-and-enforcement)
17. [Policy Review](#17-policy-review)
18. [Definitions](#18-definitions)
19. [Version Control](#19-version-control)

---

## 1. Introduction

TechCorp India is committed to safeguarding its information assets, including all electronic and physical data, systems, networks, and intellectual property. This IT Security Policy establishes the framework for maintaining a robust security posture, ensuring compliance with relevant Indian and international laws (e.g., IT Act 2000, Digital Personal Data Protection Act, 2023, GDPR where applicable), and protecting the privacy of our customers and employees. Adherence to this policy is mandatory for everyone associated with TechCorp India.

## 2. Policy Scope

This policy applies to:
*   All TechCorp India employees (full-time, part-time, temporary).
*   All contractors, consultants, interns, and vendors accessing TechCorp India's IT systems or data.
*   All IT assets owned or managed by TechCorp India, including but not limited to servers, workstations, laptops, mobile devices, networks, applications, and data stored thereon.
*   Any personal devices used to access TechCorp India resources (under BYOD guidelines).

## 3. Policy Objectives

The primary objectives of this policy are to:
*   Protect the **Confidentiality** of sensitive information from unauthorized disclosure.
*   Ensure the **Integrity** of information by safeguarding its accuracy and completeness.
*   Maintain the **Availability** of information systems and data for authorized users.
*   Minimize security risks and protect against cyber threats.
*   Establish clear responsibilities for information security across the organization.
*   Ensure compliance with legal, regulatory, and contractual obligations.
*   Foster a security-aware culture within TechCorp India.

## 4. Roles and Responsibilities

*   **Board of Directors/Senior Management:** Overall responsibility for establishing and supporting the information security program, providing necessary resources.
*   **Chief Information Security Officer (CISO):** Develop, implement, manage, and enforce the IT Security Policy. Oversee security operations, incident response, and awareness programs.
*   **IT Department:** Implement and maintain security controls, manage network and system security, ensure software updates, and provide technical support.
*   **Department Heads/Managers:** Ensure their teams understand and comply with this policy, manage access rights for their teams, and promote security awareness.
*   **All Employees, Contractors, and Third Parties:** Adhere strictly to this policy, report security incidents promptly, and actively participate in security awareness training.

## 5. General Security Principles

*   **Least Privilege:** Users shall only be granted the minimum access rights necessary to perform their job functions.
*   **Need-to-Know:** Access to sensitive information shall be granted only to individuals who require it for their official duties.
*   **Separation of Duties:** Critical tasks shall be divided among multiple individuals to prevent a single point of failure or compromise.
*   **Defense-in-Depth:** Multiple layers of security controls shall be implemented to protect information assets.
*   **Accountability:** All users are accountable for their actions on TechCorp India's IT systems.

## 6. Password Policy

> All users must adhere to the following guidelines for creating and managing passwords for TechCorp India systems.

*   **Complexity:** Passwords must:
    *   Be a minimum of 12 characters long.
    *   Include a combination of uppercase letters, lowercase letters, numbers, and special characters.
    *   Not contain easily guessable information (e.g., common words, personal names, dates of birth).
    *   Not be a variation of previous passwords.
*   **Uniqueness:** Passwords for TechCorp India systems must be unique and not reused for any personal accounts or other company systems.
*   **MFA (Multi-Factor Authentication):** Multi-Factor Authentication is mandatory for all access to TechCorp India's internal networks, critical applications, and remote access services.
*   **Storage:** Passwords must never be written down, stored in unencrypted files, or shared with anyone. Use of an approved password manager is highly recommended.
*   **Sharing:** Passwords must never be shared with colleagues, supervisors, or IT personnel. TechCorp India IT staff will never ask for your password.
*   **Frequency of Change:** Passwords must be changed every 90 days.
*   **Account Lockout:** Systems will lock accounts after a defined number of failed login attempts (e.g., 5 attempts) and require IT intervention for unlocking.

## 7. Device Usage Policy

### 7.1. Company-Owned Devices

> TechCorp India provides company-owned devices (laptops, desktops, mobile phones) for business use.

*   **Authorized Use:** Devices are primarily for business use. Limited personal use is permitted as long as it does not interfere with work duties, violate any company policy, or pose a security risk.
*   **No Unauthorized Software:** Only authorized and licensed software may be installed (refer to [Software Installation and Usage Policy](#10-software-installation-and-usage-policy)).
*   **Security Software:** All company-owned devices must have TechCorp India-approved antivirus, endpoint detection and response (EDR), and Mobile Device Management (MDM) software installed and actively running. Tampering with or disabling these security measures is strictly prohibited.
*   **Updates:** Users are responsible for ensuring their devices receive timely operating system and application updates as mandated by the IT Department.
*   **Remote Access:** All remote access to TechCorp India's internal network and resources must be conducted via approved VPN connections.
*   **Physical Security:** Devices must be physically secured (refer to [Physical Security of Devices](#73-physical-security-of-devices)).
*   **No Rooting/Jailbreaking:** Modifying the operating system of company-owned mobile devices (rooting, jailbreaking) is strictly forbidden.
*   **Return of Devices:** All company-owned devices must be returned to TechCorp India upon termination of employment or contract.

### 7.2. Bring Your Own Device (BYOD)

> Personal devices may be allowed to access TechCorp India resources under strict conditions.

*   **Approval:** Use of personal devices for company business requires explicit approval from management and the IT Department.
*   **MDM Enrollment:** Approved personal devices must be enrolled in TechCorp India's Mobile Device Management (MDM) solution. This allows the IT Department to enforce security policies (e.g., strong passwords, encryption, remote wipe capability) and access only company-related data.
*   **Data Separation:** Sensitive company data must not be stored directly on personal devices unless secured within approved enterprise applications or containers managed by MDM.
*   **Security Software:** Personal devices must have up-to-date operating systems, antivirus software (if applicable), and screen lock enabled.
*   **Remote Wipe Consent:** Users consent to the IT Department's ability to remotely wipe all TechCorp India-related data (and potentially the entire device if company data cannot be isolated) from their personal device upon termination of employment or if the device is lost/stolen or policy is violated.
*   **No Support:** TechCorp India's IT Department will provide limited support for personal devices.
*   **User Responsibility:** Users are solely responsible for the security and maintenance of their personal devices, including backups of personal data.

### 7.3. Physical Security of Devices

*   **Unattended Devices:** Devices must never be left unattended in public areas. At the office, lock your screen when away from your desk.
*   **Travel:** Exercise extreme caution when traveling with company devices. Keep them out of sight and secured.
*   **Home Security:** When working from home, ensure devices are stored securely and inaccessible to unauthorized individuals (e.g., family members, guests).
*   **Reporting Loss/Theft:** Any loss or theft of a TechCorp India device (company-owned or personal device with company data) must be reported immediately to the IT Department and your manager (refer to [Incident Reporting and Response Policy](#11-incident-reporting-and-response-policy)).

## 8. Data Classification Policy

> All information assets at TechCorp India are classified to ensure appropriate protection based on their sensitivity and impact if compromised.

### 8.1. Data Classification Levels

| Classification Level | Description                                                                        | Examples                                                                                                                                                                                                                                                                                                                                                                                                     |
| :------------------- | :--------------------------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Public**           | Information intended for public consumption. Disclosure poses no risk to TechCorp. | Marketing materials, press releases, public website content, job postings.                                                                                                                                                                                                                                                                                                                                   |
| **Internal**         | Information for internal use only. Disclosure causes minimal impact.               | Internal memos, company newsletters, non-sensitive internal reports, general employee directories (excluding contact details).                                                                                                                                                                                                                                                                               |
| **Confidential**     | Information that, if disclosed, could cause significant harm to TechCorp or its customers. Subject to NDAs. | Employee PII (salary, performance reviews), customer lists, non-public financial data, internal strategies, project plans, specific intellectual property (before patent/copyright), sensitive internal communications. **(Falls under "Sensitive Personal Data or Information" (SPDI) as per IT Act 2000 rules if it relates to a natural person)**.                                                        |
| **Restricted**       | Highly sensitive information, often legally protected. Unauthorized disclosure could result in severe financial loss, legal penalties, reputational damage, or compromise national security (if applicable). | Source code, proprietary algorithms, unfiled patents, top-secret project details, unreleased product designs, trade secrets, highly sensitive customer data (e.g., health records, credit card numbers, biometric data), critical security vulnerabilities. **(Falls under "Sensitive Personal Data or Information" (SPDI) as per IT Act 2000 rules, and subject to stricter controls under Digital Personal Data Protection Act, 2023)**. |

### 8.2. Data Handling Guidelines

*   **Ownership:** Every piece of TechCorp India data must have a designated owner (typically the department head or project manager) responsible for its classification and protection.
*   **Marking:** All data (physical and digital) must be appropriately marked with its classification level.
*   **Storage:**
    *   **Public/Internal:** May be stored on standard network drives, internal platforms.
    *   **Confidential:** Must be stored on secure, access-controlled network drives. Encryption at rest is highly recommended.
    *   **Restricted:** Must be stored on highly secured, encrypted, and access-controlled systems. Often requires specialized storage solutions.
*   **Access:** Access must be granted based on the "Least Privilege" and "Need-to-Know" principles.
*   **Transmission:**
    *   **Public/Internal:** Standard email, internal chat.
    *   **Confidential:** Internal email, secure file transfer. External transmission must be encrypted.
    *   **Restricted:** Secure, end-to-end encrypted channels only. External transmission requires explicit CISO approval and strong encryption.
*   **Disposal:**
    *   **Public/Internal:** Standard deletion.
    *   **Confidential/Restricted:** Secure deletion or physical destruction (shredding, degaussing, data wiping) as per TechCorp India's data retention policy.
*   **Data Minimization:** Collect and retain only the data absolutely necessary for business purposes and for the minimum required duration.
*   **Privacy by Design:** Incorporate data protection considerations into the design of all systems and processes.

## 9. Email Usage Policy

> This policy governs the use of TechCorp India's email system for all employees and contractors.

*   **Professional Conduct:** Email communications must be professional and reflect TechCorp India's values.
*   **No Unlawful Content:** Do not send or forward emails containing illegal, offensive, discriminatory, harassing, or sexually explicit content.
*   **Confidentiality:**
    *   Exercise caution when sending sensitive or confidential information via email.
    *   **Never** send Restricted data via unencrypted email, internally or externally.
    *   External transmission of Confidential data should be encrypted and/or password-protected where feasible.
    *   Verify recipient addresses before sending sensitive information.
*   **Phishing & Spam:**
    *   Be vigilant for phishing attempts. Do not click on suspicious links or open attachments from unknown senders.
    *   Report all suspected phishing emails to `security@techcorp.in`.
    *   Do not send unsolicited bulk emails (spam).
*   **Attachments:** Be cautious about opening unexpected attachments, even from known senders, as they may contain malware.
*   **Monitoring:** Users should be aware that TechCorp India's email system is company property and is subject to monitoring for security, compliance, and legal purposes, as permitted by law.
*   **Archiving & Retention:** Emails are subject to TechCorp India's data retention policies.
*   **Personal Use:** Limited personal use is permissible as long as it does not interfere with work, consume excessive resources, or violate other company policies.

## 10. Software Installation and Usage Policy

> This policy outlines the guidelines for installing and using software on TechCorp India's IT assets.

*   **Authorized Software Only:** Only software explicitly approved and licensed by TechCorp India may be installed on company-owned devices.
*   **No Unauthorized Installation:** Users are strictly prohibited from installing any software (including freeware, shareware, trial versions, or pirated software) without prior authorization from the IT Department.
*   **Licensing Compliance:** All software must be legally licensed. Installing or using unlicensed software is a serious violation and illegal.
*   **Source of Software:** Approved software must be installed only from official, trusted sources provided or sanctioned by the IT Department.
*   **Administrator Rights:** Users will typically not have local administrator rights on their company devices. Requests for elevated privileges or specific software installations must be submitted to the IT Department.
*   **Updates:** Users must ensure that their operating systems and approved applications are regularly updated as directed by the IT Department to apply security patches.
*   **Malicious Software:** Users must not download, install, or knowingly use any software that could be considered malicious (e.g., spyware, adware, viruses, keyloggers) or bypass security controls.
*   **Cloud Applications:** Use of third-party cloud applications for storing or processing company data requires explicit approval and security vetting by the IT Department and CISO.

## 11. Incident Reporting and Response Policy

> This policy details the procedures for reporting and responding to IT security incidents.

*   **What is an Incident?** An IT security incident is any event that could compromise the confidentiality, integrity, or availability of TechCorp India's information assets. This includes, but is not limited to:
    *   Suspected or actual data breach/leakage.
    *   Loss or theft of a company device or a personal device containing company data.
    *   Unauthorized access to systems or data.
    *   Malware infection (virus, ransomware, spyware).
    *   Successful phishing attacks.
    *   Suspicious emails, pop-ups, or system behavior.
    *   Denial of Service (DoS) attacks.
    *   Weak or compromised passwords.
*   **When to Report:** All incidents, suspected or actual, must be reported **immediately** upon discovery. Delaying reporting can exacerbate the damage.
*   **How to Report:**
    *   **Primary Channel:** Email `security@techcorp.in` or call the IT Helpdesk **(ext. XXXX)**.
    *   **Provide Details:** When reporting, provide as much detail as possible, including:
        *   Your name and contact information.
        *   Date and time of the incident.
        *   Description of the incident (what happened, what you observed).
        *   System(s) affected (e.g., laptop serial number, application name).
        *   Any actions taken so far.
*   **User Actions During an Incident:**
    *   **Do NOT try to fix it yourself** unless specifically instructed by IT/Security.
    *   **Do NOT shut down or restart affected systems** unless instructed, as this can destroy forensic evidence. Disconnect from the network if possible.
    *   Preserve any evidence (e.g., screenshots, error messages).
    *   Cooperate fully with the incident response team.
*   **Incident Response Team (IRT) Role:**
    *   The CISO leads the IRT.
    *   The IRT will investigate, contain, eradicate, recover from, and conduct post-incident analysis.
    *   The IRT is responsible for notifying affected parties and regulatory bodies, if required by law.
*   **No Blame Culture:** TechCorp India fosters a "no blame" culture for reporting incidents. The priority is to resolve the incident and learn from it, not to assign blame, unless gross negligence or malicious intent is evident.

## 12. Access Control Policy

> This policy governs access to TechCorp India's physical and logical IT assets.

*   **Principle of Least Privilege:** Access to systems, applications, and data will be granted only to the extent necessary to perform job functions.
*   **Unique User IDs:** Each user will have a unique user ID. Sharing of user IDs is strictly prohibited.
*   **Role-Based Access Control (RBAC):** Access will be managed through defined roles with associated permissions.
*   **Regular Review:** User access rights will be reviewed at least quarterly or upon job role changes/termination.
*   **Physical Access:** Access to server rooms, data centers, and other critical infrastructure is restricted to authorized personnel only, controlled by access cards, biometric systems, or logs.
*   **Remote Access:** All remote access must utilize TechCorp India's approved VPN solutions with MFA.

## 13. Network Security Policy

> This policy covers the security measures for TechCorp India's internal and external networks.

*   **Firewalls:** All network perimeters and critical internal segments will be protected by firewalls.
*   **Intrusion Detection/Prevention Systems (IDS/IPS):** IDS/IPS will be deployed to monitor and protect against network intrusions.
*   **Network Segmentation:** Networks will be segmented to isolate critical systems and data.
*   **Wireless Networks:** All wireless networks must be secured using strong encryption (e.g., WPA3 Enterprise) and authentication. Guest Wi-Fi will be isolated from the corporate network.
*   **Vulnerability Scanning:** Regular vulnerability scans and penetration testing will be conducted on network infrastructure.

## 14. Third-Party and Vendor Access Policy

> This policy governs the security requirements for third parties and vendors who access TechCorp India's systems or data.

*   **Security Agreements:** All third parties and vendors accessing TechCorp India's systems or data must sign a Non-Disclosure Agreement (NDA) and a security addendum outlining their security responsibilities and compliance requirements.
*   **Least Privilege:** Access granted to third parties will be limited to the specific systems and data required for their services.
*   **Secure Access:** Third-party access must utilize secure, monitored channels (e.g., dedicated VPN, jump boxes) and multi-factor authentication.
*   **Auditing:** TechCorp India reserves the right to audit third-party security controls and practices.
*   **Data Protection:** Third parties are responsible for protecting TechCorp India's data in their care according to its classification level and applicable laws.

## 15. Security Awareness and Training

> TechCorp India is committed to fostering a strong security culture.

*   **Mandatory Training:** All new employees, contractors, and relevant third parties must complete mandatory IT security awareness training during onboarding.
*   **Annual Refresher:** Annual refresher training will be provided to all personnel to keep them informed about current threats and best practices.
*   **Targeted Training:** Specific training will be provided for roles with higher security responsibilities.
*   **Communication:** Regular security advisories and tips will be communicated via internal channels.

## 16. Compliance and Enforcement

*   **Monitoring:** TechCorp India reserves the right to monitor all network traffic, system usage, and data to ensure compliance with this policy and for security purposes, as permitted by applicable laws.
*   **Violations:** Any violation of this policy may result in disciplinary action, up to and including termination of employment or contract, and potential legal action.
*   **Legal Implications:** TechCorp India will cooperate fully with law enforcement agencies in investigating any illegal activities involving its IT assets.

## 17. Policy Review

This IT Security Policy will be reviewed at least annually by the CISO, IT Department, and Legal Department. It may also be updated as required by changes in technology, business operations, or legal/regulatory requirements.

## 18. Definitions

*   **IT Act 2000:** Information Technology Act, 2000 (and subsequent amendments) of India, governing cybersecurity and data protection.
*   **Digital Personal Data Protection Act, 2023:** India's comprehensive data protection law.
*   **GDPR:** General Data Protection Regulation (EU 2016/679), relevant if TechCorp India processes personal data of EU residents.
*   **IT Asset:** Any information, system, device, network, or facility that stores, processes, or transmits TechCorp India's information.
*   **Sensitive Data:** Information that requires specific protection due to its confidential nature, legal requirements, or potential impact if compromised.
*   **PII:** Personally Identifiable Information (e.g., name, address, phone number, email, Aadhaar number).
*   **SPDI:** Sensitive Personal Data or Information (as defined by IT Act 2000 rules, includes passwords, financial info, health info, biometric info, sexual orientation).
*   **MFA (Multi-Factor Authentication):** A security system that requires more than one method of authentication from independent categories of credentials to verify the user's identity.
*   **MDM (Mobile Device Management):** Software used to enforce security policies on mobile devices.
*   **VPN (Virtual Private Network):** A secure tunnel over a public network, used for remote access to private networks.
*   **CISO:** Chief Information Security Officer.
*   **Incident:** Any event that could compromise the confidentiality, integrity, or availability of TechCorp India's information assets.

## 19. Version Control

| Version | Date         | Author(s)        | Changes Made                               |
| :------ | :----------- | :--------------- | :----------------------------------------- |
| 1.0     | 2023-10-27   | CISO Team        | Initial Draft                              |
|         |              |                  |                                            |
|         |              |                  |                                            |

---