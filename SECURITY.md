# Security Policy

## Supported Versions

Currently, this project is in active development. Security updates will be provided for the latest version of the codebase.

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public GitHub issue
2. Email the maintainer directly or use GitHub's private vulnerability reporting feature
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will acknowledge receipt of your report within 48 hours and provide an update on the status of the vulnerability within 7 days.

## Security Considerations

### API Keys

- **Never commit API keys to the repository**
- Use `.env` file (which is gitignored) for local development
- Use environment variables or secret management systems in production
- Rotate API keys immediately if they are accidentally exposed

### CORS Configuration

- Default CORS settings are permissive for local development
- **For production deployments**, configure CORS via environment variables:
  - `CORS_ORIGINS`: Comma-separated list of allowed origins
  - `CORS_METHODS`: Allowed HTTP methods
  - `CORS_HEADERS`: Allowed headers
  - `CORS_CREDENTIALS`: Whether to allow credentials

### File System Access

- The application reads/writes to `data/conversations/` directory
- Ensure proper file permissions are set
- Validate file paths to prevent directory traversal attacks
- Consider using a database for production deployments instead of JSON files

### Dependency Security

- Regularly update dependencies using `uv sync` and `npm install`
- Review Dependabot security alerts
- Run `pip-audit` for Python dependencies and `npm audit` for Node dependencies
- Keep lockfiles (`uv.lock`, `package-lock.json`) up to date

### Input Validation

- User queries are sent directly to LLM APIs via OpenRouter
- The application does not sanitize user input before sending to LLMs
- Be aware that user input may be logged or stored in conversation history
- Consider implementing input validation for production use

### Authentication

- **Currently, no authentication is required** - the API is designed for local development
- For production deployments, implement proper authentication and authorization
- Consider rate limiting to prevent abuse

## Best Practices

1. **Never commit secrets**: Use `.env` files or secret management systems
2. **Keep dependencies updated**: Regularly review and update dependencies
3. **Review code changes**: Use code review processes before merging
4. **Monitor logs**: Review application logs for suspicious activity
5. **Use HTTPS**: Always use HTTPS in production deployments
6. **Limit network exposure**: Don't expose the API to the public internet without proper security measures

## Security Updates

Security updates will be released as needed. Check the repository for the latest version and update accordingly.

## Contact

For security concerns, please use GitHub's private vulnerability reporting feature or contact the repository maintainer directly.

