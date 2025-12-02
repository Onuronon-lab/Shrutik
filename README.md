## Development

This is the deployment-dev branch. All code should be merged and pull requested here before going to the master branch.

### Development Workflow

1. Create feature branch from `deployment-dev`
2. Implement changes with tests
3. Run tests and linting
4. Submit pull request to `deployment-dev`
5. After review and approval, merge to `deployment-dev`

## License

By contributing to Shrutik, you agree that your contributions will be licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License. This ensures that all contributions remain available for educational and non-commercial use while requiring attribution to the original creators.

## Support

For issues or questions:

- File an issue in the project repository
- Check logs in `logs/` directory
- Review error messages in database: `SELECT * FROM export_batches WHERE status = 'failed'`
- Contact system administrator
