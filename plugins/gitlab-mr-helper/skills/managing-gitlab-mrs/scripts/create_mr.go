package main

import (
	"flag"
	"fmt"
	"os"
	"os/exec"
	"strings"

	"gitlab-mr-helper/lib"
)

func main() {
	// Flags
	sourceBranch := flag.String("source", "", "Source branch (default: current branch)")
	targetBranch := flag.String("target", "main", "Target branch")
	title := flag.String("title", "", "MR title (default: derived from branch name)")
	description := flag.String("description", "", "MR description")
	labels := flag.String("labels", "", "Comma-separated labels")
	removeSource := flag.Bool("remove-source-branch", false, "Remove source branch after merge")
	auto := flag.Bool("auto", false, "Auto-detect project from git remote")

	flag.Parse()

	// Get configuration
	config, err := lib.GetConfig()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}

	// Get project path
	var projectPath string
	if *auto {
		projectPath, err = lib.GetProjectFromGit()
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error resolving project: %v\n", err)
			os.Exit(1)
		}
		fmt.Printf("✓ Project: %s\n", projectPath)
	} else {
		projectPath = flag.Arg(0)
		if projectPath == "" {
			fmt.Fprintf(os.Stderr, "Error: project path required (use --auto or provide as argument)\n")
			os.Exit(1)
		}
	}

	// Get current branch if source not specified
	source := *sourceBranch
	if source == "" {
		cmd := exec.Command("git", "rev-parse", "--abbrev-ref", "HEAD")
		output, err := cmd.Output()
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error getting current branch: %v\n", err)
			os.Exit(1)
		}
		source = strings.TrimSpace(string(output))
	}

	// Generate title from branch name if not specified
	mrTitle := *title
	if mrTitle == "" {
		mrTitle = generateTitleFromBranch(source)
	}

	// Parse labels
	var labelList []string
	if *labels != "" {
		labelList = strings.Split(*labels, ",")
		for i, l := range labelList {
			labelList[i] = strings.TrimSpace(l)
		}
	}

	// Create MR request
	req := &lib.CreateMRRequest{
		SourceBranch:       source,
		TargetBranch:       *targetBranch,
		Title:              mrTitle,
		Description:        *description,
		Labels:             labelList,
		RemoveSourceBranch: *removeSource,
	}

	fmt.Printf("Creating MR: %s → %s\n", source, *targetBranch)
	fmt.Printf("  Title: %s\n", mrTitle)

	// Create API client and submit
	client := lib.NewClient(config)
	mr, err := client.CreateMR(projectPath, req)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error creating MR: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("\n✓ MR !%d created successfully\n", mr.IID)
	fmt.Printf("  URL: %s\n", mr.WebURL)
	fmt.Printf("  State: %s\n", mr.State)
}

func generateTitleFromBranch(branch string) string {
	// Remove common prefixes
	branch = strings.TrimPrefix(branch, "feature/")
	branch = strings.TrimPrefix(branch, "fix/")
	branch = strings.TrimPrefix(branch, "bugfix/")
	branch = strings.TrimPrefix(branch, "hotfix/")

	// Replace separators with spaces
	branch = strings.ReplaceAll(branch, "-", " ")
	branch = strings.ReplaceAll(branch, "_", " ")

	// Capitalize first letter
	if len(branch) > 0 {
		branch = strings.ToUpper(string(branch[0])) + branch[1:]
	}

	return branch
}
