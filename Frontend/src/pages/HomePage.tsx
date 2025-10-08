import {
  ArrowRight,
  Activity,
  BarChart3,
  Compass,
  Gauge,
  Globe2,
  LineChart,
  Quote,
  Satellite,
  Waves,
  Menu,
  X
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { useState, useEffect, useRef } from 'react';

// Video URL - using public directory
const videoUrl = '/video.mp4';

interface HomePageProps {
  onEnter?: () => void;
}

const metrics = [
  { label: 'Ocean Regions Monitored', value: '120+', icon: Globe2 },
  { label: 'Marine Assets Tracked', value: '18K', icon: Satellite },
  { label: 'Live Sensor Streams', value: '34M', icon: Activity },
  { label: 'Insights Delivered Weekly', value: '250K', icon: LineChart }
];

const features = [
  {
    title: 'Unified Ocean Intelligence',
    description:
      'Bring satellite, buoy, and vessel data together to produce consistent, multi-layered situational awareness.',
    icon: Waves
  },
  {
    title: 'Predictive Climate Models',
    description:
      'Deploy FloatChat’s AI copilots to simulate thermal fronts, salinity shifts, and cyclonic risks before they happen.',
    icon: BarChart3
  },
  {
    title: 'Operational Playbooks',
    description:
      'Generate compliance-ready briefs, voyage routing guidance, and mitigation playbooks for every stakeholder.',
    icon: Compass
  }
];

const testimonials = [
  {
    quote:
      'FloatChat has become our mission control for ocean operations. The AI surfaces the exact risks we need to monitor.',
    name: 'Dr. Radhika Menon',
    role: 'Head of Marine Analytics, BlueWave Consortium'
  },
  {
    quote:
      'We reduced incident response time by 43% because FloatChat converts raw telemetry into actionable alerts instantly.',
    name: 'Leo Fernandez',
    role: 'Director of Fleet Operations, OceanMotion'
  }
];

const integrations = [
  'Copernicus Marine',
  'NOAA ERDDAP',
  'GOES & INSAT',
  'AIS Providers',
  'ARGO Floats',
  'CMEMS',
  'GFW Datasets'
];

export function HomePage({ onEnter }: HomePageProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [videoError, setVideoError] = useState<string | null>(null);
  const [videoLoaded, setVideoLoaded] = useState(false);

  useEffect(() => {
    if (videoRef.current) {
      // Log the video URL being used
      console.log('Video element found');
      console.log('Video URL from import:', videoUrl);
      console.log('Direct path:', '/video.mp4');
      
      // Try multiple sources
      const sources = [videoUrl, '/video.mp4', './video.mp4'];
      
      const tryNextSource = (index: number) => {
        if (index >= sources.length) {
          setVideoError('All video sources failed');
          return;
        }
        
        const source = sources[index];
        console.log(`Trying video source ${index + 1}/${sources.length}:`, source);
        
        if (videoRef.current) {
          videoRef.current.src = source;
          videoRef.current.load();
          
          videoRef.current.play().then(() => {
            console.log('Video playing successfully with source:', source);
            setVideoLoaded(true);
            setVideoError(null);
          }).catch(err => {
            console.error(`Failed to play video from ${source}:`, err);
            tryNextSource(index + 1);
          });
        }
      };
      
      // Start trying sources
      tryNextSource(0);
    }
  }, []);

  return (
    <div className="relative min-h-screen bg-[#04060f] text-white overflow-hidden">
      {/* Video Background Container */}
      <div className="absolute inset-0 w-full h-full">
        <video
          ref={videoRef}
          className="absolute top-0 left-0 min-w-full min-h-full w-auto h-auto object-cover"
          autoPlay
          loop
          muted
          playsInline
          poster="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='1920' height='1080'%3E%3Crect fill='%2304060f' width='1920' height='1080'/%3E%3C/svg%3E"
          onLoadedData={() => {
            console.log('Video loaded successfully');
            setVideoLoaded(true);
          }}
          onError={(e) => {
            console.error('Video error event:', e);
            const video = e.currentTarget as HTMLVideoElement;
            if (video.error) {
              console.error('Video error details:', {
                code: video.error.code,
                message: video.error.message
              });
            }
          }}
        />
        
        {/* Fallback video with direct source */}
        {videoError && (
          <video
            className="absolute top-0 left-0 min-w-full min-h-full w-auto h-auto object-cover"
            autoPlay
            loop
            muted
            playsInline
            src="/video.mp4"
          />
        )}
        
        {/* Debug info */}
        {(videoError || !videoLoaded) && (
          <div className="absolute top-20 left-4 bg-red-500/80 text-white p-2 rounded z-50">
            {videoError ? `Video Error: ${videoError}` : 'Loading video...'}
          </div>
        )}
        
        {/* Overlay gradients */}
        <div className="absolute inset-0 bg-[#04060f]/40" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.12),_transparent_55%),radial-gradient(circle_at_bottom,_rgba(14,116,144,0.16),_transparent_60%)]" />
      </div>

      <header className="sticky top-0 z-50 backdrop-blur-lg bg-[#04060f]/80 border-b border-white/10">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-6">
          <div className="text-lg font-semibold tracking-wide">
            <span className="bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent">FloatChat</span>
          </div>
          
          {/* Desktop Navigation */}
          <nav className="hidden items-center space-x-10 text-sm font-medium text-gray-300 md:flex">
            <a className="transition hover:text-white" href="#mission">Mission</a>
            <a className="transition hover:text-white" href="#features">Capabilities</a>
            <a className="transition hover:text-white" href="#insights">Insights</a>
            <a className="transition hover:text-white" href="#partners">Partners</a>
          </nav>
          
          <div className="hidden items-center gap-4 md:flex">
            <Link
              to="/dashboard"
              className="rounded-full border border-white/15 px-4 py-1.5 text-sm text-gray-200 transition hover:border-white/30 hover:text-white"
            >
              Dashboard
            </Link>
            <Link
              to="/chat"
              onClick={onEnter}
              className="flex items-center gap-2 rounded-full bg-white/15 px-4 py-1.5 text-sm font-semibold text-white transition hover:bg-white/25"
            >
              Launch FloatChat <ArrowRight className="h-4 w-4" />
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 text-gray-300 hover:text-white transition"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-white/10 bg-[#04060f]/95 backdrop-blur-lg">
            <nav className="flex flex-col px-6 py-4 space-y-4">
              <a 
                className="text-sm font-medium text-gray-300 transition hover:text-white" 
                href="#mission"
                onClick={() => setMobileMenuOpen(false)}
              >
                Mission
              </a>
              <a 
                className="text-sm font-medium text-gray-300 transition hover:text-white" 
                href="#features"
                onClick={() => setMobileMenuOpen(false)}
              >
                Capabilities
              </a>
              <a 
                className="text-sm font-medium text-gray-300 transition hover:text-white" 
                href="#insights"
                onClick={() => setMobileMenuOpen(false)}
              >
                Insights
              </a>
              <a 
                className="text-sm font-medium text-gray-300 transition hover:text-white" 
                href="#partners"
                onClick={() => setMobileMenuOpen(false)}
              >
                Partners
              </a>
              <div className="pt-4 space-y-3 border-t border-white/10">
                <Link
                  to="/dashboard"
                  onClick={() => setMobileMenuOpen(false)}
                  className="w-full rounded-full border border-white/15 px-4 py-2 text-sm text-gray-200 transition hover:border-white/30 hover:text-white"
                >
                 Dashboard
                </Link>
                <Link
                  to="/chat"
                  onClick={() => {
                    setMobileMenuOpen(false);
                    onEnter?.();
                  }}
                  className="flex items-center justify-center gap-2 w-full rounded-full bg-white/15 px-4 py-2 text-sm font-semibold text-white transition hover:bg-white/25"
                >
                  Launch FloatChat <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            </nav>
          </div>
        )}
      </header>

      <main className="relative mx-auto flex w-full max-w-6xl flex-col px-6 z-10">
        <section id="mission" className="pt-12 pb-20">
          <div className="max-w-3xl">
            <span className="rounded-full border border-white/10 px-3 py-1 text-xs uppercase tracking-[0.35em] text-blue-200/80">
              Ocean Intelligence Platform
            </span>
            <h1 className="mt-6 text-4xl font-semibold leading-tight md:text-6xl">
              Understand the planet’s oceans in real time — with an AI copilot built for maritime decision makers.
            </h1>
            <p className="mt-6 max-w-2xl text-base text-gray-300 md:text-lg">
              FloatChat fuses live telemetry, historic climatology, and predictive modelling to reveal what your vessels,
              energy assets, and coastal communities will face next. Ask questions in natural language and receive
              clear, defensible actions.
            </p>
            <div className="mt-10 flex flex-col gap-4 sm:flex-row">
              <Link
                to="/chat"
                onClick={onEnter}
                className="flex items-center justify-center gap-3 rounded-full bg-gradient-to-r from-blue-500 to-cyan-400 px-6 py-3 text-sm font-semibold text-white shadow-[0_20px_35px_-20px_rgba(14,165,233,0.6)] transition hover:from-blue-400 hover:to-cyan-300"
              >
                Dive into the console <ArrowRight className="h-4 w-4" />
              </Link>
              <button className="rounded-full border border-white/15 px-6 py-3 text-sm font-semibold text-gray-200 transition hover:border-white/30 hover:text-white">
                Download product brief
              </button>
            </div>
          </div>

          <div className="mt-16 grid gap-6 rounded-3xl border border-white/10 bg-white/[0.04] p-8 sm:grid-cols-2 lg:grid-cols-4">
            {metrics.map(({ label, value, icon: Icon }) => (
              <div key={label} className="rounded-2xl border border-white/5 bg-black/30 p-6">
                <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-full bg-white/10">
                  <Icon className="h-5 w-5 text-cyan-300" />
                </div>
                <p className="text-3xl font-semibold text-white">{value}</p>
                <p className="mt-2 text-sm text-gray-400">{label}</p>
              </div>
            ))}
          </div>
        </section>

        <section id="features" className="py-20">
          <div className="flex flex-col gap-12 lg:flex-row">
            <div className="flex-1">
              <span className="text-xs uppercase tracking-[0.3em] text-cyan-300/80">Capabilities</span>
              <h2 className="mt-4 text-3xl font-semibold md:text-4xl">From raw telemetry to mission-grade intelligence</h2>
              <p className="mt-4 text-base text-gray-300">
                FloatChat orchestrates ingestion, cleansing, and reasoning across thousands of data streams. Every insight is
                versioned, auditable, and ready for operational deployment.
              </p>
            </div>
            <div className="flex flex-1 flex-col gap-6">
              {features.map(({ title, description, icon: Icon }) => (
                <div key={title} className="rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur">
                  <div className="flex items-start gap-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-cyan-500/15">
                      <Icon className="h-5 w-5 text-cyan-300" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-white">{title}</h3>
                      <p className="mt-2 text-sm text-gray-300">{description}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="insights" className="py-20">
          <div className="grid gap-12 rounded-3xl border border-white/10 bg-gradient-to-br from-white/[0.08] to-transparent p-10 lg:grid-cols-2">
            <div>
              <span className="text-xs uppercase tracking-[0.3em] text-cyan-200/80">Actionable Insights</span>
              <h2 className="mt-4 text-3xl font-semibold md:text-4xl">Operational foresight for every ocean vertical</h2>
              <p className="mt-4 text-base text-gray-200">
                Review orchestrated dashboards for offshore energy, shipping, coastal security, search & rescue, and climate
                research. FloatChat explains anomalies in plain language and gives you mitigation sequences in seconds.
              </p>
              <ul className="mt-8 space-y-4 text-sm text-gray-300">
                <li className="flex items-start gap-3">
                  <Gauge className="mt-[2px] h-4 w-4 text-cyan-300" />
                  <span>Live stability indexes for rigs, cables, and marine protected areas.</span>
                </li>
                <li className="flex items-start gap-3">
                  <BarChart3 className="mt-[2px] h-4 w-4 text-cyan-300" />
                  <span>Scenario playbooks that quantify impact, probability, and recommended actions.</span>
                </li>
                <li className="flex items-start gap-3">
                  <Compass className="mt-[2px] h-4 w-4 text-cyan-300" />
                  <span>Voyage routing copilots that account for weather, currents, emissions, and cost.</span>
                </li>
              </ul>
            </div>
            <div className="rounded-3xl border border-white/5 bg-black/40 p-8 backdrop-blur">
              <h3 className="text-lg font-semibold text-white">Intelligence timeline</h3>
              <div className="mt-6 space-y-6 text-sm text-gray-300">
                <div>
                  <p className="text-cyan-300">00:00 • Satellite ingest</p>
                  <p className="mt-1">New Sentinel-6 pass detects anomalous sea surface heights in Arabian Sea zone 19.</p>
                </div>
                <div>
                  <p className="text-cyan-300">00:04 • AI assessment</p>
                  <p className="mt-1">FloatChat flags potential Kelvin wave event; confidence 86%. Suggested notifications issued.</p>
                </div>
                <div>
                  <p className="text-cyan-300">00:06 • Recommended action</p>
                  <p className="mt-1">Adjust drilling schedules, deploy Argo float cluster, and alert coastal security command.</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="partners" className="py-20">
          <div className="rounded-3xl border border-white/10 bg-white/[0.03] p-10 text-center">
            <span className="text-xs uppercase tracking-[0.3em] text-cyan-200/70">Ecosystem</span>
            <h2 className="mt-4 text-3xl font-semibold md:text-4xl">Plug into the sources you already trust</h2>
            <p className="mt-4 text-base text-gray-300">
              Seamless ingest and governance across public, commercial, and proprietary feeds. Reduce integration overheads and
              maintain compliance with your data policies.
            </p>
            <div className="mt-8 flex flex-wrap items-center justify-center gap-4 text-sm text-gray-200">
              {integrations.map((name) => (
                <span key={name} className="rounded-full border border-white/10 px-4 py-2">
                  {name}
                </span>
              ))}
            </div>
          </div>
        </section>

        <section className="py-20">
          <div className="grid gap-10 lg:grid-cols-2">
            {testimonials.map(({ quote, name, role }) => (
              <div key={name} className="rounded-3xl border border-white/10 bg-white/[0.04] p-8 text-left shadow-[0_30px_60px_-40px_rgba(59,130,246,0.4)]">
                <Quote className="h-6 w-6 text-cyan-200" />
                <p className="mt-6 text-lg text-gray-100">{quote}</p>
                <div className="mt-6 text-sm text-gray-400">
                  <p className="font-semibold text-white">{name}</p>
                  <p>{role}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="pb-16">
          <div className="rounded-3xl border border-white/10 bg-gradient-to-r from-blue-600/40 via-cyan-500/40 to-emerald-400/40 p-10 text-center shadow-[0_40px_80px_-48px_rgba(14,165,233,0.75)]">
            <h2 className="text-3xl font-semibold text-white md:text-4xl">Ready to orchestrate ocean intelligence for your organisation?</h2>
            <p className="mt-4 text-base text-gray-100">
              Schedule a strategy session with our specialists or dive straight into FloatChat to explore the AI-powered console.
            </p>
            <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Link
                to="/chat"
                onClick={onEnter}
                className="flex items-center gap-3 rounded-full bg-white px-6 py-3 text-sm font-semibold text-[#04060f] transition hover:bg-gray-100"
              >
                Open FloatChat Console <ArrowRight className="h-4 w-4" />
              </Link>
              <button className="rounded-full border border-white/60 px-6 py-3 text-sm font-semibold text-white transition hover:border-white">
                Talk to sales
              </button>
            </div>
          </div>
        </section>
      </main>

      <footer className="relative mx-auto w-full max-w-6xl border-t border-white/10 px-6 py-6 text-sm text-gray-400 z-10">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-base font-semibold text-white">FloatChat</p>
            <p className="mt-1 max-w-sm text-xs text-gray-400">
              Built by ocean scientists, data engineers, and AI researchers to accelerate sustainable maritime operations.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            <a className="hover:text-white" href="#privacy">Privacy</a>
            <a className="hover:text-white" href="#terms">Terms</a>
            <a className="hover:text-white" href="#status">Status</a>
            <a className="hover:text-white" href="#contact">Contact</a>
          </div>
        </div>
        <p className="mt-4 text-xs text-gray-500">© {new Date().getFullYear()} FloatChat Labs. All rights reserved.</p>
      </footer>
    </div>
  );
}
