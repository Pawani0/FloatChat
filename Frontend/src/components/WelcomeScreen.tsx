import { Waves, TrendingUp, Map, Activity, Sparkles } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface WelcomeScreenProps {
  onSuggestedPrompt: (prompt: string) => void;
}

export function WelcomeScreen({ onSuggestedPrompt }: WelcomeScreenProps) {
  const suggestedPrompts = [
    {
      icon: TrendingUp,
      title: "Temperature Profile",
      prompt: "Show me a temperature profile from the Arabian Sea",
      description: "Vertical temperature distribution with depth",
      badge: "Popular"
    },
    {
      icon: Activity,
      title: "T-S Diagram",
      prompt: "Generate a T-S diagram for Arabian Sea water masses",
      description: "Temperature-Salinity relationship analysis",
      badge: "Advanced"
    },
    {
      icon: Map,
      title: "Float Trajectory",
      prompt: "Show Argo float trajectory in the Arabian Sea",
      description: "Track float movement over time",
      badge: "Tracking"
    },
    {
      icon: Waves,
      title: "Salinity Time Series",
      prompt: "Display salinity time series from Argo data",
      description: "Temporal variation in salinity measurements",
      badge: "Time Series"
    }
  ];

  return (
    <div className="flex min-h-[calc(100vh-300px)] items-center justify-center">
      <div className="w-full max-w-4xl space-y-8">
        {/* Hero section */}
        <div className="space-y-4 text-center">
          <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-500 shadow-xl shadow-blue-500/30">
            <Waves className="h-8 w-8 text-white" />
          </div>
          <div>
            <h1 className="text-4xl font-bold tracking-tight text-white">
              What would you like to explore?
            </h1>
            <p className="mt-3 text-lg text-gray-400">
              Ask me about oceanographic data with AI-powered analysis
            </p>
          </div>
        </div>

        {/* Suggested prompts grid */}
        <div className="grid gap-4 sm:grid-cols-2">
          {suggestedPrompts.map((prompt, index) => {
            const IconComponent = prompt.icon;
            return (
              <Card
                key={index}
                className="group cursor-pointer border-white/10 bg-white/[0.03] transition-all hover:border-cyan-400/40 hover:bg-white/[0.06] hover:shadow-lg hover:shadow-cyan-500/10"
                onClick={() => onSuggestedPrompt(prompt.prompt)}
              >
                <CardHeader className="space-y-3">
                  <div className="flex items-start justify-between">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-white/10 transition-colors group-hover:bg-cyan-500/20">
                      <IconComponent className="h-5 w-5 text-cyan-400" />
                    </div>
                    <Badge variant="secondary" className="bg-white/5 text-xs text-gray-400 hover:bg-white/10">
                      {prompt.badge}
                    </Badge>
                  </div>
                  <div>
                    <CardTitle className="text-base text-white">
                      {prompt.title}
                    </CardTitle>
                    <CardDescription className="mt-1.5 text-sm text-gray-400">
                      {prompt.description}
                    </CardDescription>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-xs text-cyan-300/80 line-clamp-2">
                    "{prompt.prompt}"
                  </p>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Additional info */}
        <Card className="border-white/5 bg-white/[0.02]">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-blue-400" />
              <div className="space-y-1 text-sm">
                <p className="text-gray-300">
                  <span className="font-semibold text-white">Try asking:</span> "Pacific Ocean temperature trends", 
                  "Analyze El Niño patterns", "Gulf Stream current data", or "Mediterranean salinity gradients"
                </p>
                <p className="text-xs text-gray-500">
                  FloatChat specializes in oceanographic data analysis with temperature, salinity, and float trajectory visualization.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}