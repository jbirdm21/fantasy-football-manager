import React from 'react';
import Link from 'next/link';

export default function Home() {
  return (
    <div className="space-y-8">
      <section className="py-12 text-center">
        <h1 className="text-4xl font-bold mb-4">Ultimate Personal Fantasy Football Manager</h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Your personal assistant to dominate fantasy football leagues on ESPN and Yahoo
        </p>
      </section>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <FeatureCard 
          title="Draft-Day War Room" 
          description="Value-based drafting, tier breakdowns, and real-time league sync"
          icon="📊"
          href="/draft"
        />
        <FeatureCard 
          title="Roster Optimization" 
          description="Weekly start/sit advice, waiver recommendations, and rest-of-season value"
          icon="🔄"
          href="/roster"
        />
        <FeatureCard 
          title="Trade Machine" 
          description="Fair value engine, injury risk assessment, and schedule strength analysis"
          icon="🔀"
          href="/trade"
        />
        <FeatureCard 
          title="In-Game Coach" 
          description="Live win probability models and tilt-proof swap alerts"
          icon="🏈"
          href="/live"
        />
        <FeatureCard 
          title="League Management" 
          description="Connect your ESPN and Yahoo leagues"
          icon="🔑"
          href="/leagues"
        />
        <FeatureCard 
          title="Player Analysis" 
          description="Deep statistics and trend analysis"
          icon="📈"
          href="/players"
        />
      </div>
    </div>
  );
}

function FeatureCard({ 
  title, 
  description, 
  icon,
  href
}: { 
  title: string; 
  description: string; 
  icon: string;
  href: string;
}) {
  return (
    <Link href={href}>
      <div className="bg-card text-card-foreground rounded-lg border shadow-sm p-6 hover:shadow-md transition-shadow">
        <div className="text-4xl mb-4">{icon}</div>
        <h3 className="text-xl font-semibold mb-2">{title}</h3>
        <p className="text-muted-foreground">{description}</p>
      </div>
    </Link>
  );
} 