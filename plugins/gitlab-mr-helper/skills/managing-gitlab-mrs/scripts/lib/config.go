package lib

import (
	"bufio"
	"fmt"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

// Config holds GitLab connection configuration
type Config struct {
	Token     string
	URL       string
	ProjectID string
}

// GetConfig retrieves GitLab configuration from environment and git
func GetConfig() (*Config, error) {
	config := &Config{}

	// Get token from environment or credential files
	token, err := getToken()
	if err != nil {
		return nil, err
	}
	config.Token = token

	// Get GitLab URL (default or from environment)
	config.URL = os.Getenv("GITLAB_URL")
	if config.URL == "" {
		config.URL = "https://gitlab.com"
	}
	config.URL = strings.TrimSuffix(config.URL, "/")

	return config, nil
}

// GetProjectFromGit resolves project path from git remote
func GetProjectFromGit() (string, error) {
	cmd := exec.Command("git", "remote", "get-url", "origin")
	output, err := cmd.Output()
	if err != nil {
		return "", fmt.Errorf("failed to get git remote: %w", err)
	}

	remoteURL := strings.TrimSpace(string(output))
	return parseProjectPath(remoteURL)
}

func parseProjectPath(remoteURL string) (string, error) {
	// Handle SSH URLs: git@gitlab.com:group/project.git
	if strings.HasPrefix(remoteURL, "git@") {
		parts := strings.SplitN(remoteURL, ":", 2)
		if len(parts) != 2 {
			return "", fmt.Errorf("invalid SSH remote URL: %s", remoteURL)
		}
		path := strings.TrimSuffix(parts[1], ".git")
		return path, nil
	}

	// Handle HTTPS URLs: https://gitlab.com/group/project.git
	u, err := url.Parse(remoteURL)
	if err != nil {
		return "", fmt.Errorf("failed to parse remote URL: %w", err)
	}

	path := strings.TrimPrefix(u.Path, "/")
	path = strings.TrimSuffix(path, ".git")
	return path, nil
}

func getToken() (string, error) {
	// 1. Check environment variable
	if token := os.Getenv("GITLAB_TOKEN"); token != "" {
		return token, nil
	}

	// 2. Check .netrc file
	if token := getTokenFromNetrc(); token != "" {
		return token, nil
	}

	// 3. Check .git-credentials
	if token := getTokenFromGitCredentials(); token != "" {
		return token, nil
	}

	return "", fmt.Errorf("no GitLab token found. Set GITLAB_TOKEN environment variable or configure ~/.netrc or ~/.git-credentials")
}

func getTokenFromNetrc() string {
	home, err := os.UserHomeDir()
	if err != nil {
		return ""
	}

	netrcPath := filepath.Join(home, ".netrc")
	file, err := os.Open(netrcPath)
	if err != nil {
		return ""
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	var inGitlab bool
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		fields := strings.Fields(line)

		for i := 0; i < len(fields); i++ {
			switch fields[i] {
			case "machine":
				if i+1 < len(fields) && strings.Contains(fields[i+1], "gitlab") {
					inGitlab = true
				} else {
					inGitlab = false
				}
			case "password":
				if inGitlab && i+1 < len(fields) {
					return fields[i+1]
				}
			}
		}
	}
	return ""
}

func getTokenFromGitCredentials() string {
	home, err := os.UserHomeDir()
	if err != nil {
		return ""
	}

	credPath := filepath.Join(home, ".git-credentials")
	file, err := os.Open(credPath)
	if err != nil {
		return ""
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if strings.Contains(line, "gitlab") {
			u, err := url.Parse(line)
			if err != nil {
				continue
			}
			if password, ok := u.User.Password(); ok {
				return password
			}
		}
	}
	return ""
}
