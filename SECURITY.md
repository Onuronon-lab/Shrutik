# Security Policy

## Our Commitment to Security

The Shrutik team takes the security of our platform seriously. We appreciate the efforts of security researchers and community members who help us maintain a secure environment for all users. This document outlines our security policy, including how to report vulnerabilities and what to expect from our response process.

## Supported Versions

We provide security updates for the following versions of Shrutik:

| Version | Supported          | Notes                                    |
| ------- | ------------------ | ---------------------------------------- |
| 1.0.x   | ✅ | Current stable release, actively maintained |
| < 1.0   | :x:                | Pre-release versions, no longer supported |

**Note**: We recommend always using the latest stable version to ensure you have the most recent security patches and improvements.

## Reporting a Vulnerability

If you discover a security vulnerability in Shrutik, please report it responsibly. We kindly ask that you do not publicly disclose the issue until we have had a chance to address it.

### How to Report

**Primary Contact Method:**
- **Email**: onuronon.dev@gmail.com
- **Subject Line**: [SECURITY] Brief description of the issue

**Alternative Contact Method:**
- **Discord**: Join our [Discord server](https://discord.gg/9hZ9eW8ARk) and send a direct message to a moderator or administrator requesting a private security discussion channel

### What to Include in Your Report

To help us understand and address the issue quickly, please include the following information:

1. **Description**: A clear description of the vulnerability
2. **Impact**: The potential impact and severity of the issue
3. **Steps to Reproduce**: Detailed steps to reproduce the vulnerability
4. **Proof of Concept**: If applicable, include code, screenshots, or other evidence
5. **Affected Components**: Which parts of the system are affected (backend, frontend, database, etc.)
6. **Environment Details**: 
   - Shrutik version
   - Deployment method (Docker, local, etc.)
   - Operating system
   - Browser (for frontend issues)
7. **Suggested Fix**: If you have ideas for how to fix the issue, we'd love to hear them

### Response Timeline

We are committed to responding to security reports in a timely manner:

- **Initial Acknowledgment**: Within 48 hours of receiving your report
- **Status Update**: Within 7 days with an assessment of the issue and expected timeline
- **Resolution**: Varies based on severity and complexity, but we aim to:
  - **Critical vulnerabilities**: Patch within 7-14 days
  - **High severity**: Patch within 14-30 days
  - **Medium/Low severity**: Patch in the next scheduled release

We will keep you informed throughout the process and notify you when the issue has been resolved.

## Disclosure Policy

### Responsible Disclosure

We follow a coordinated disclosure process:

1. **Private Reporting**: Security issues are reported privately to our team
2. **Investigation**: We investigate and develop a fix
3. **Patch Release**: We release a security patch
4. **Public Disclosure**: After the patch is released and users have had time to update (typically 7-14 days), we may publish details about the vulnerability
5. **Credit**: With your permission, we will credit you in our security advisories and release notes

### Public Disclosure Timeline

- We will not publicly disclose security issues until a fix is available
- We ask that security researchers also refrain from public disclosure until we have released a patch
- If you plan to publish details about the vulnerability, please coordinate with us on timing

## What Constitutes a Security Vulnerability

### Security Issues (Please Report)

The following are considered security vulnerabilities and should be reported through our security process:

- **Authentication/Authorization Bypass**: Ability to access resources without proper authentication or with insufficient permissions
- **SQL Injection**: Ability to execute arbitrary SQL queries
- **Cross-Site Scripting (XSS)**: Ability to inject malicious scripts into the application
- **Cross-Site Request Forgery (CSRF)**: Ability to perform unauthorized actions on behalf of authenticated users
- **Remote Code Execution (RCE)**: Ability to execute arbitrary code on the server
- **Path Traversal**: Ability to access files outside of intended directories
- **Sensitive Data Exposure**: Unintended exposure of passwords, tokens, API keys, or personal information
- **Insecure Direct Object References**: Ability to access other users' data by manipulating identifiers
- **Server-Side Request Forgery (SSRF)**: Ability to make the server perform unintended requests
- **Privilege Escalation**: Ability to gain higher privileges than intended
- **Security Misconfiguration**: Critical misconfigurations that expose the system to attacks
- **Cryptographic Vulnerabilities**: Weak encryption, insecure random number generation, or other cryptographic issues

### General Bugs (Please Use GitHub Issues)

The following are not considered security vulnerabilities and should be reported as regular issues on GitHub:

- **Feature Requests**: Suggestions for new security features
- **Performance Issues**: Slow response times or resource consumption (unless they enable DoS attacks)
- **UI/UX Bugs**: Visual or usability issues that don't expose sensitive data
- **Documentation Errors**: Typos or inaccuracies in documentation
- **Compatibility Issues**: Problems with specific browsers, OS versions, or configurations
- **Rate Limiting Bypass**: Unless it enables significant abuse or DoS attacks
- **Information Disclosure**: Minor information leaks that don't expose sensitive data (e.g., version numbers, technology stack)
- **Denial of Service**: Issues requiring unrealistic resources or conditions (unless easily exploitable)

**When in Doubt**: If you're unsure whether an issue is a security vulnerability, please report it through our security process. We'd rather review it privately than have a potential vulnerability disclosed publicly.

## Security Best Practices for Users

To help keep your Shrutik installation secure:

### For Administrators

1. **Keep Updated**: Always run the latest stable version of Shrutik
2. **Strong Passwords**: Use strong, unique passwords for all accounts, especially admin accounts
3. **Environment Variables**: Never commit `.env` files or expose sensitive configuration
4. **HTTPS**: Always use HTTPS in production environments
5. **Database Security**: Secure your PostgreSQL database with strong passwords and network restrictions
6. **Redis Security**: Configure Redis with authentication and restrict network access
7. **Regular Backups**: Maintain regular backups of your database and uploaded files
8. **Monitor Logs**: Regularly review application and system logs for suspicious activity
9. **Rate Limiting**: Configure appropriate rate limits for your use case
10. **Access Control**: Follow the principle of least privilege when assigning user roles

### For Contributors

1. **Code Review**: All code changes should be reviewed before merging
2. **Dependencies**: Keep dependencies up to date and review security advisories
3. **Input Validation**: Always validate and sanitize user input
4. **Secure Coding**: Follow secure coding practices and OWASP guidelines
5. **Secrets Management**: Never commit secrets, API keys, or credentials to the repository
6. **Testing**: Include security considerations in your testing

## Security Features

Shrutik includes several built-in security features:

- **JWT-based Authentication**: Secure token-based authentication system
- **Role-Based Access Control (RBAC)**: Granular permissions for different user roles
- **Password Hashing**: Secure password storage using industry-standard hashing
- **Rate Limiting**: Protection against brute force and DoS attacks
- **Input Validation**: Comprehensive validation of all user inputs
- **CORS Configuration**: Proper cross-origin resource sharing controls
- **SQL Injection Protection**: Parameterized queries via SQLAlchemy ORM
- **File Upload Validation**: Strict validation of uploaded audio files
- **Secure Session Management**: Proper session handling and token expiration
- **Audit Logging**: Comprehensive logging of security-relevant events

## Recognition

We believe in recognizing the contributions of security researchers who help us improve Shrutik's security:

- **Security Advisories**: We will credit you in our security advisories (with your permission)
- **Release Notes**: Your contribution will be acknowledged in release notes
- **Hall of Fame**: We maintain a list of security researchers who have responsibly disclosed vulnerabilities

If you prefer to remain anonymous, please let us know in your report.

## Questions?

If you have questions about this security policy or need clarification on what constitutes a security issue, please contact us at onuronon.dev@gmail.com or join our [Discord server](https://discord.gg/9hZ9eW8ARk).

Thank you for helping keep Shrutik and our community safe!

---

**Last Updated**: November 2025
