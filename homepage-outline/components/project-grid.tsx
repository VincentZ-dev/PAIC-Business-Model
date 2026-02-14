"use client";

import { LayoutGrid, List } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ProjectCard, type Project } from "@/components/project-card";

// Sample data - replace with your actual data source
const sampleProjects: Project[] = [
  {
    id: "1",
    title: "Q4 Financial Report",
    description:
      "Quarterly financial analysis with revenue breakdowns and projections for the upcoming fiscal year.",
    pageCount: 24,
    lastModified: "Jan 15, 2026",
    tags: ["Finance", "Reports", "Q4"],
  },
  {
    id: "2",
    title: "Product Roadmap 2026",
    description:
      "Strategic product planning document outlining key features and milestones.",
    pageCount: 18,
    lastModified: "Jan 12, 2026",
    tags: ["Strategy", "Product"],
  },
  {
    id: "3",
    title: "User Research Summary",
    description:
      "Compiled user research findings from interviews and surveys conducted in December.",
    pageCount: 32,
    lastModified: "Jan 10, 2026",
    tags: ["Research", "UX"],
  },
  {
    id: "4",
    title: "Marketing Campaign Brief",
    description:
      "Spring campaign overview with target demographics and channel strategies.",
    pageCount: 12,
    lastModified: "Jan 8, 2026",
    tags: ["Marketing"],
  },
  {
    id: "5",
    title: "Technical Documentation",
    description:
      "API documentation and integration guides for the platform SDK.",
    pageCount: 45,
    lastModified: "Jan 5, 2026",
    tags: ["Technical", "API", "SDK"],
  },
  {
    id: "6",
    title: "Brand Guidelines v3",
    description:
      "Updated brand identity guidelines including new color palette and typography rules.",
    pageCount: 28,
    lastModified: "Jan 3, 2026",
    tags: ["Design", "Brand"],
  },
];

export function ProjectGrid() {
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [sortBy, setSortBy] = useState("recent");

  return (
    <section className="py-8">
      {/* Header */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">
            Saved Projects
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {sampleProjects.length} projects in your library
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Select value={sortBy} onValueChange={setSortBy}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="recent">Recently Modified</SelectItem>
              <SelectItem value="name">Name</SelectItem>
              <SelectItem value="pages">Page Count</SelectItem>
            </SelectContent>
          </Select>

          <div className="flex items-center rounded-lg border border-border p-1">
            <Button
              variant={viewMode === "grid" ? "secondary" : "ghost"}
              size="icon"
              className="h-8 w-8"
              onClick={() => setViewMode("grid")}
            >
              <LayoutGrid className="h-4 w-4" />
              <span className="sr-only">Grid view</span>
            </Button>
            <Button
              variant={viewMode === "list" ? "secondary" : "ghost"}
              size="icon"
              className="h-8 w-8"
              onClick={() => setViewMode("list")}
            >
              <List className="h-4 w-4" />
              <span className="sr-only">List view</span>
            </Button>
          </div>
        </div>
      </div>

      {/* Grid */}
      <div
        className={
          viewMode === "grid"
            ? "grid gap-6 sm:grid-cols-2 lg:grid-cols-3"
            : "flex flex-col gap-4"
        }
      >
        {sampleProjects.map((project) => (
          <ProjectCard key={project.id} project={project} />
        ))}
      </div>
    </section>
  );
}
