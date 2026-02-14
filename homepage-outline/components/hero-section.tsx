import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";

export function HeroSection() {
  return (
    <section className="relative overflow-hidden py-16 sm:py-24">
      {/* Subtle background pattern */}
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(0,0,0,0.02)_0%,transparent_50%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_80%,rgba(0,0,0,0.02)_0%,transparent_50%)]" />
      </div>

      <div className="text-center">
        <h1 className="mx-auto max-w-3xl text-balance text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
          Your PDF projects,
          <br />
          <span className="text-muted-foreground">organized beautifully</span>
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-pretty text-lg text-muted-foreground">
          Save, organize, and access your PDF documents with ease. Create
          snapshots, add tags, and find what you need instantly.
        </p>
        <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
          <Button size="lg" className="gap-2">
            Get Started
            <ArrowRight className="h-4 w-4" />
          </Button>
          <Button size="lg" variant="outline">
            Learn More
          </Button>
        </div>

        {/* Stats */}
        <div className="mt-16 flex flex-wrap items-center justify-center gap-8 border-t border-border pt-8 sm:gap-16">
          <div className="text-center">
            <p className="text-3xl font-semibold">1,000+</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Documents Saved
            </p>
          </div>
          <div className="text-center">
            <p className="text-3xl font-semibold">50+</p>
            <p className="mt-1 text-sm text-muted-foreground">Collections</p>
          </div>
          <div className="text-center">
            <p className="text-3xl font-semibold">99.9%</p>
            <p className="mt-1 text-sm text-muted-foreground">Uptime</p>
          </div>
        </div>
      </div>
    </section>
  );
}
