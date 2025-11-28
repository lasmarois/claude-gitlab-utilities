package main

import (
	"flag"
	"fmt"
	"os"
	"strconv"
	"strings"

	"gitlab-mr-helper/lib"
)

func main() {
	// Flags
	mrIID := flag.Int("mr", 0, "Merge request IID (required)")
	title := flag.String("title", "", "New MR title")
	description := flag.String("description", "", "New MR description")
	targetBranch := flag.String("target", "", "New target branch")
	labels := flag.String("labels", "", "Comma-separated labels (replaces existing)")
	stateEvent := flag.String("state", "", "State event: close, reopen")
	auto := flag.Bool("auto", false, "Auto-detect project from git remote")

	flag.Parse()

	// Validate MR IID
	if *mrIID == 0 {
		// Try to get from positional argument
		if flag.NArg() > 0 {
			iid, err := strconv.Atoi(flag.Arg(0))
			if err == nil {
				*mrIID = iid
			}
		}
		if *mrIID == 0 {
			fmt.Fprintf(os.Stderr, "Error: --mr <iid> is required\n")
			os.Exit(1)
		}
	}

	// Check if any update fields provided
	if *title == "" && *description == "" && *targetBranch == "" && *labels == "" && *stateEvent == "" {
		fmt.Fprintf(os.Stderr, "Error: at least one update field required (--title, --description, --target, --labels, --state)\n")
		os.Exit(1)
	}

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
		// Look for project in remaining args after MR IID
		for i := 0; i < flag.NArg(); i++ {
			arg := flag.Arg(i)
			if _, err := strconv.Atoi(arg); err != nil {
				projectPath = arg
				break
			}
		}
		if projectPath == "" {
			fmt.Fprintf(os.Stderr, "Error: project path required (use --auto or provide as argument)\n")
			os.Exit(1)
		}
	}

	// Build update request
	req := &lib.UpdateMRRequest{}
	var updates []string

	if *title != "" {
		req.Title = *title
		updates = append(updates, fmt.Sprintf("title → %q", *title))
	}
	if *description != "" {
		req.Description = *description
		updates = append(updates, "description updated")
	}
	if *targetBranch != "" {
		req.TargetBranch = *targetBranch
		updates = append(updates, fmt.Sprintf("target → %s", *targetBranch))
	}
	if *labels != "" {
		labelList := strings.Split(*labels, ",")
		for i, l := range labelList {
			labelList[i] = strings.TrimSpace(l)
		}
		req.Labels = labelList
		updates = append(updates, fmt.Sprintf("labels → [%s]", *labels))
	}
	if *stateEvent != "" {
		req.StateEvent = *stateEvent
		updates = append(updates, fmt.Sprintf("state → %s", *stateEvent))
	}

	fmt.Printf("Updating MR !%d:\n", *mrIID)
	for _, u := range updates {
		fmt.Printf("  • %s\n", u)
	}

	// Create API client and update
	client := lib.NewClient(config)
	mr, err := client.UpdateMR(projectPath, *mrIID, req)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error updating MR: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("\n✓ MR !%d updated successfully\n", mr.IID)
	fmt.Printf("  Title: %s\n", mr.Title)
	fmt.Printf("  State: %s\n", mr.State)
	fmt.Printf("  URL: %s\n", mr.WebURL)
}
