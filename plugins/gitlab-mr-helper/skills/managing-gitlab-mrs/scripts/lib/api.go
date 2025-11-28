package lib

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"time"
)

// MergeRequest represents a GitLab merge request
type MergeRequest struct {
	ID           int    `json:"id"`
	IID          int    `json:"iid"`
	Title        string `json:"title"`
	Description  string `json:"description"`
	State        string `json:"state"`
	SourceBranch string `json:"source_branch"`
	TargetBranch string `json:"target_branch"`
	WebURL       string `json:"web_url"`
	Author       struct {
		Username string `json:"username"`
	} `json:"author"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
	Draft     bool      `json:"draft"`
	Labels    []string  `json:"labels"`
}

// CreateMRRequest represents the request body for creating an MR
type CreateMRRequest struct {
	SourceBranch       string   `json:"source_branch"`
	TargetBranch       string   `json:"target_branch"`
	Title              string   `json:"title"`
	Description        string   `json:"description,omitempty"`
	Labels             []string `json:"labels,omitempty"`
	AssigneeIDs        []int    `json:"assignee_ids,omitempty"`
	ReviewerIDs        []int    `json:"reviewer_ids,omitempty"`
	RemoveSourceBranch bool     `json:"remove_source_branch,omitempty"`
}

// UpdateMRRequest represents the request body for updating an MR
type UpdateMRRequest struct {
	Title        string   `json:"title,omitempty"`
	Description  string   `json:"description,omitempty"`
	TargetBranch string   `json:"target_branch,omitempty"`
	Labels       []string `json:"labels,omitempty"`
	StateEvent   string   `json:"state_event,omitempty"` // close, reopen
}

// Client wraps the GitLab API
type Client struct {
	config     *Config
	httpClient *http.Client
}

// NewClient creates a new GitLab API client
func NewClient(config *Config) *Client {
	return &Client{
		config: config,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// CreateMR creates a new merge request
func (c *Client) CreateMR(projectPath string, req *CreateMRRequest) (*MergeRequest, error) {
	endpoint := fmt.Sprintf("%s/api/v4/projects/%s/merge_requests", c.config.URL, url.PathEscape(projectPath))

	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", endpoint, bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	c.setHeaders(httpReq)

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to execute request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusCreated {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(bodyBytes))
	}

	var mr MergeRequest
	if err := json.NewDecoder(resp.Body).Decode(&mr); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &mr, nil
}

// ListMRs lists merge requests for a project
func (c *Client) ListMRs(projectPath string, state string, limit int) ([]MergeRequest, error) {
	endpoint := fmt.Sprintf("%s/api/v4/projects/%s/merge_requests", c.config.URL, url.PathEscape(projectPath))

	u, err := url.Parse(endpoint)
	if err != nil {
		return nil, fmt.Errorf("failed to parse endpoint: %w", err)
	}

	q := u.Query()
	if state != "" {
		q.Set("state", state)
	}
	if limit > 0 {
		q.Set("per_page", fmt.Sprintf("%d", limit))
	}
	u.RawQuery = q.Encode()

	httpReq, err := http.NewRequest("GET", u.String(), nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	c.setHeaders(httpReq)

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to execute request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(bodyBytes))
	}

	var mrs []MergeRequest
	if err := json.NewDecoder(resp.Body).Decode(&mrs); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return mrs, nil
}

// UpdateMR updates an existing merge request
func (c *Client) UpdateMR(projectPath string, mrIID int, req *UpdateMRRequest) (*MergeRequest, error) {
	endpoint := fmt.Sprintf("%s/api/v4/projects/%s/merge_requests/%d", c.config.URL, url.PathEscape(projectPath), mrIID)

	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	httpReq, err := http.NewRequest("PUT", endpoint, bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	c.setHeaders(httpReq)

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to execute request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(bodyBytes))
	}

	var mr MergeRequest
	if err := json.NewDecoder(resp.Body).Decode(&mr); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &mr, nil
}

// GetMR gets a single merge request by IID
func (c *Client) GetMR(projectPath string, mrIID int) (*MergeRequest, error) {
	endpoint := fmt.Sprintf("%s/api/v4/projects/%s/merge_requests/%d", c.config.URL, url.PathEscape(projectPath), mrIID)

	httpReq, err := http.NewRequest("GET", endpoint, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	c.setHeaders(httpReq)

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to execute request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, string(bodyBytes))
	}

	var mr MergeRequest
	if err := json.NewDecoder(resp.Body).Decode(&mr); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &mr, nil
}

func (c *Client) setHeaders(req *http.Request) {
	req.Header.Set("PRIVATE-TOKEN", c.config.Token)
	req.Header.Set("Content-Type", "application/json")
}
