package main

import (
	"flag"
	"fmt"
	"os"
	"strings"
	"time"

	"gitlab-mr-helper/lib"
)

func main() {
	// Flags
	state := flag.String("state", "opened", "MR state: opened, closed, merged, all")
	limit := flag.Int("limit", 20, "Maximum number of MRs to list")
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
		fmt.Printf("✓ Project: %s\n\n", projectPath)
	} else {
		projectPath = flag.Arg(0)
		if projectPath == "" {
			fmt.Fprintf(os.Stderr, "Error: project path required (use --auto or provide as argument)\n")
			os.Exit(1)
		}
	}

	// Create API client and list MRs
	client := lib.NewClient(config)
	mrs, err := client.ListMRs(projectPath, *state, *limit)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error listing MRs: %v\n", err)
		os.Exit(1)
	}

	if len(mrs) == 0 {
		fmt.Printf("No merge requests found (state: %s)\n", *state)
		return
	}

	fmt.Printf("Merge Requests (%s):\n", *state)
	fmt.Println(strings.Repeat("-", 80))

	for _, mr := range mrs {
		stateIcon := getStateIcon(mr.State)
		draftPrefix := ""
		if mr.Draft {
			draftPrefix = "[Draft] "
		}

		age := formatAge(mr.CreatedAt)

		fmt.Printf("%s !%d  %s%s\n", stateIcon, mr.IID, draftPrefix, mr.Title)
		fmt.Printf("     %s → %s  |  @%s  |  %s\n",
			mr.SourceBranch, mr.TargetBranch, mr.Author.Username, age)

		if len(mr.Labels) > 0 {
			fmt.Printf("     Labels: %s\n", strings.Join(mr.Labels, ", "))
		}
		fmt.Println()
	}

	fmt.Printf("Total: %d merge request(s)\n", len(mrs))
}

func getStateIcon(state string) string {
	switch state {
	case "opened":
		return "🟢"
	case "merged":
		return "🟣"
	case "closed":
		return "🔴"
	default:
		return "⚪"
	}
}

func formatAge(t time.Time) string {
	duration := time.Since(t)

	if duration < time.Hour {
		return fmt.Sprintf("%dm ago", int(duration.Minutes()))
	} else if duration < 24*time.Hour {
		return fmt.Sprintf("%dh ago", int(duration.Hours()))
	} else if duration < 7*24*time.Hour {
		return fmt.Sprintf("%dd ago", int(duration.Hours()/24))
	} else {
		return t.Format("Jan 2, 2006")
	}
}
