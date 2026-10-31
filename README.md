![Banner](banner.png)

# cha-InsecureDefaultConfigReporter
Checks a YAML or JSON configuration file for two built-in default password values: the password setting set to 'password' and the admin_password setting set to 'admin'. Uses pyyaml to parse configuration files and, when the user supplies a JSON schema file, jsonschema to validate the configuration against that user supplied schema. No other built-in checks ship in this tool: it does not check ports or access controls.

## Install
`git clone https://github.com/ShadowStrikeHQ/cha-insecuredefaultconfigreporter`

## Usage
`./cha-insecuredefaultconfigreporter [params]`

## Parameters
- `-h`: Show help message and exit
- `-s`: Path to the JSON schema file for validation.
- `-t`: No description provided
- `-l`: No description provided

## License
Copyright (c) ShadowStrikeHQ
