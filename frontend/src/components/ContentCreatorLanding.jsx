import { useState } from "react";
import { 
  Sparkles, 
  FileText, 
  Video, 
  Share2, 
  TrendingUp, 
  Users, 
  CheckCircle2,
  ArrowRight,
  Zap,
  Target,
  BarChart3,
  Globe,
  PenTool,
  PlayCircle,
  Mail,
  Search,
  Layers,
  Brain,
  Shield,
  Rocket,
  X
} from "lucide-react";
import Login from "./Login";
import "./ContentCreatorLanding.css";

function ContentCreatorLanding({ onShowLogin }) {
  const [email, setEmail] = useState("");
  const [showLoginModal, setShowLoginModal] = useState(false);

  const handleGetStarted = () => {
    if (onShowLogin) {
      onShowLogin();
    } else {
      setShowLoginModal(true);
    }
  };

  const handleEmailSubmit = (e) => {
    e.preventDefault();
    // Handle email signup - show login modal
    handleGetStarted();
  };

  return (
    <div className="content-creator-landing">
      {/* Header Navigation */}
      <header className="landing-header">
        <div className="container">
          <div className="header-content">
            <div className="header-brand">
              <Sparkles className="header-logo" />
              <span className="header-brand-name">Accordant</span>
            </div>
            <nav className="header-nav">
              <a href="#how-it-works" className="nav-link">How It Works</a>
              <a href="#content-types" className="nav-link">Features</a>
              <a href="#use-cases" className="nav-link">Use Cases</a>
              <button className="nav-login-btn" onClick={handleGetStarted}>
                Login
              </button>
              <button className="nav-cta-btn" onClick={handleGetStarted}>
                Get Started
                <ArrowRight className="nav-cta-icon" />
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-background">
          <div className="gradient-orb orb-1"></div>
          <div className="gradient-orb orb-2"></div>
          <div className="gradient-orb orb-3"></div>
        </div>
        <div className="container">
          <div className="hero-content">
            <div className="hero-badge">
              <Sparkles className="badge-icon" />
              <span>Powered by Accordant LLM Council</span>
            </div>
            <h1 className="hero-title">
              Create Content That Converts
              <span className="gradient-text"> Across Every Platform</span>
            </h1>
            <p className="hero-description">
              Meet your Content Creator AI Council—a team of specialized AI personalities 
              that collaborate to produce blog posts, video scripts, social content, and more. 
              Get multiple perspectives, peer-reviewed quality, and synthesized excellence in every piece.
            </p>
            <div className="hero-cta-group">
              <button className="cta-primary" onClick={handleGetStarted}>
                Start Creating Free
                <ArrowRight className="cta-icon" />
              </button>
              <button className="cta-secondary" onClick={() => document.getElementById('how-it-works').scrollIntoView({ behavior: 'smooth' })}>
                See How It Works
              </button>
            </div>
            <div className="hero-stats">
              <div className="stat-item">
                <div className="stat-number">3-Stage</div>
                <div className="stat-label">Deliberation Process</div>
              </div>
              <div className="stat-item">
                <div className="stat-number">Multiple</div>
                <div className="stat-label">AI Perspectives</div>
              </div>
              <div className="stat-item">
                <div className="stat-number">Peer-Reviewed</div>
                <div className="stat-label">Quality Assurance</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="how-it-works-section">
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">How Accordant Council Works</h2>
            <p className="section-subtitle">
              Unlike single AI tools, Accordant uses a collaborative council of AI personalities 
              that debate, review, and synthesize the best answer for you.
            </p>
          </div>
          <div className="process-steps">
            <div className="process-step">
              <div className="step-number">1</div>
              <div className="step-icon-wrapper">
                <Users className="step-icon" />
              </div>
              <h3 className="step-title">Multiple Perspectives</h3>
              <p className="step-description">
                Your content request goes to multiple specialized AI personalities simultaneously. 
                Each provides their unique take—from creative angles to SEO optimization.
              </p>
            </div>
            <div className="process-connector">
              <ArrowRight className="connector-icon" />
            </div>
            <div className="process-step">
              <div className="step-number">2</div>
              <div className="step-icon-wrapper">
                <Target className="step-icon" />
              </div>
              <h3 className="step-title">Peer Review</h3>
              <p className="step-description">
                Each AI reviews the others' work anonymously, ranking quality and identifying strengths. 
                This ensures bias-free evaluation and catches what you might miss.
              </p>
            </div>
            <div className="process-connector">
              <ArrowRight className="connector-icon" />
            </div>
            <div className="process-step">
              <div className="step-number">3</div>
              <div className="step-icon-wrapper">
                <Brain className="step-icon" />
              </div>
              <h3 className="step-title">Synthesized Excellence</h3>
              <p className="step-description">
                The Chairman AI synthesizes all perspectives and reviews into one comprehensive, 
                high-quality piece that combines the best of every approach.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Content Types Section */}
      <section id="content-types" className="content-types-section">
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">Create Any Content Type</h2>
            <p className="section-subtitle">
              From long-form articles to viral social posts, your Content Creator Council adapts to every format.
            </p>
          </div>
          <div className="content-types-grid">
            <div className="content-type-card">
              <div className="card-icon-wrapper">
                <FileText className="card-icon" />
              </div>
              <h3 className="card-title">Blog Posts & Articles</h3>
              <p className="card-description">
                SEO-optimized long-form content, pillar articles, and comprehensive guides that drive organic traffic.
              </p>
              <ul className="card-features">
                <li><CheckCircle2 className="feature-icon" /> Keyword optimization</li>
                <li><CheckCircle2 className="feature-icon" /> Internal linking</li>
                <li><CheckCircle2 className="feature-icon" /> Scannable structure</li>
              </ul>
            </div>
            <div className="content-type-card">
              <div className="card-icon-wrapper">
                <Video className="card-icon" />
              </div>
              <h3 className="card-title">Video Scripts</h3>
              <p className="card-description">
                Engaging YouTube scripts, TikTok content, and webinar presentations with hooks that capture attention.
              </p>
              <ul className="card-features">
                <li><CheckCircle2 className="feature-icon" /> Retention optimization</li>
                <li><CheckCircle2 className="feature-icon" /> Platform-specific formats</li>
                <li><CheckCircle2 className="feature-icon" /> Strong CTAs</li>
              </ul>
            </div>
            <div className="content-type-card">
              <div className="card-icon-wrapper">
                <Share2 className="card-icon" />
              </div>
              <h3 className="card-title">Social Media Content</h3>
              <p className="card-description">
                Platform-optimized posts for LinkedIn, Instagram, Twitter, and more. Native formatting for maximum engagement.
              </p>
              <ul className="card-features">
                <li><CheckCircle2 className="feature-icon" /> Platform-specific tone</li>
                <li><CheckCircle2 className="feature-icon" /> Optimal length</li>
                <li><CheckCircle2 className="feature-icon" /> Engagement hooks</li>
              </ul>
            </div>
            <div className="content-type-card">
              <div className="card-icon-wrapper">
                <Mail className="card-icon" />
              </div>
              <h3 className="card-title">Email Campaigns</h3>
              <p className="card-description">
                Compelling newsletters, automation sequences, and conversion-focused email content.
              </p>
              <ul className="card-features">
                <li><CheckCircle2 className="feature-icon" /> Subject line optimization</li>
                <li><CheckCircle2 className="feature-icon" /> Mobile-first design</li>
                <li><CheckCircle2 className="feature-icon" /> Clear CTAs</li>
              </ul>
            </div>
            <div className="content-type-card">
              <div className="card-icon-wrapper">
                <Layers className="card-icon" />
              </div>
              <h3 className="card-title">Content Repurposing</h3>
              <p className="card-description">
                Transform one piece into multiple formats. Extract micro-content, create infographics, and build content series.
              </p>
              <ul className="card-features">
                <li><CheckCircle2 className="feature-icon" /> Multi-format extraction</li>
                <li><CheckCircle2 className="feature-icon" /> Content multiplication</li>
                <li><CheckCircle2 className="feature-icon" /> Series planning</li>
              </ul>
            </div>
            <div className="content-type-card">
              <div className="card-icon-wrapper">
                <Search className="card-icon" />
              </div>
              <h3 className="card-title">SEO Strategy</h3>
              <p className="card-description">
                Keyword research, content clusters, meta descriptions, and comprehensive SEO optimization.
              </p>
              <ul className="card-features">
                <li><CheckCircle2 className="feature-icon" /> Keyword research</li>
                <li><CheckCircle2 className="feature-icon" /> Content clusters</li>
                <li><CheckCircle2 className="feature-icon" /> Topical authority</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="benefits-section">
        <div className="container">
          <div className="benefits-content">
            <div className="benefits-text">
              <h2 className="section-title">Why Choose Accordant Council?</h2>
              <p className="section-subtitle">
                Get the collective intelligence of multiple AI specialists working together, 
                not just one AI trying to do everything.
              </p>
              <div className="benefits-list">
                <div className="benefit-item">
                  <Zap className="benefit-icon" />
                  <div className="benefit-content">
                    <h3 className="benefit-title">Multiple Perspectives</h3>
                    <p className="benefit-description">
                      Each AI personality brings unique expertise—creative angles, SEO focus, 
                      conversion optimization, and more.
                    </p>
                  </div>
                </div>
                <div className="benefit-item">
                  <Shield className="benefit-icon" />
                  <div className="benefit-content">
                    <h3 className="benefit-title">Quality Assurance</h3>
                    <p className="benefit-description">
                      Peer review process catches errors, identifies gaps, and ensures 
                      your content meets the highest standards.
                    </p>
                  </div>
                </div>
                <div className="benefit-item">
                  <BarChart3 className="benefit-icon" />
                  <div className="benefit-content">
                    <h3 className="benefit-title">Optimized for Results</h3>
                    <p className="benefit-description">
                      Content is crafted with SEO, engagement, and conversion metrics in mind 
                      from the start.
                    </p>
                  </div>
                </div>
                <div className="benefit-item">
                  <Globe className="benefit-icon" />
                  <div className="benefit-content">
                    <h3 className="benefit-title">Cross-Platform Mastery</h3>
                    <p className="benefit-description">
                      Adapt your core message across platforms while maintaining brand consistency 
                      and platform-specific best practices.
                    </p>
                  </div>
                </div>
              </div>
            </div>
            <div className="benefits-visual">
              <div className="visual-card">
                <div className="visual-header">
                  <div className="visual-avatar-group">
                    <div className="avatar avatar-1">C</div>
                    <div className="avatar avatar-2">S</div>
                    <div className="avatar avatar-3">O</div>
                  </div>
                  <div className="visual-title">Council in Action</div>
                </div>
                <div className="visual-content">
                  <div className="visual-message">
                    <div className="message-author">Creative Director</div>
                    <div className="message-text">"Let's use storytelling to hook readers..."</div>
                  </div>
                  <div className="visual-message">
                    <div className="message-author">SEO Strategist</div>
                    <div className="message-text">"We need to optimize for 'content marketing'..."</div>
                  </div>
                  <div className="visual-message">
                    <div className="message-author">Conversion Expert</div>
                    <div className="message-text">"The CTA should be more prominent..."</div>
                  </div>
                  <div className="visual-synthesis">
                    <Brain className="synthesis-icon" />
                    <div className="synthesis-text">Synthesizing best approach...</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Use Cases Section */}
      <section id="use-cases" className="use-cases-section">
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">Perfect For</h2>
            <p className="section-subtitle">
              Whether you're a solo creator or part of a team, Accordant scales with your needs.
            </p>
          </div>
          <div className="use-cases-grid">
            <div className="use-case-card">
              <PenTool className="use-case-icon" />
              <h3 className="use-case-title">Content Creators</h3>
              <p className="use-case-description">
                Scale your content production without sacrificing quality. 
                Get multiple AI perspectives on every piece.
              </p>
            </div>
            <div className="use-case-card">
              <TrendingUp className="use-case-icon" />
              <h3 className="use-case-title">Marketing Teams</h3>
              <p className="use-case-description">
                Maintain brand consistency across platforms while optimizing 
                for each channel's unique requirements.
              </p>
            </div>
            <div className="use-case-card">
              <Rocket className="use-case-icon" />
              <h3 className="use-case-title">Startups</h3>
              <p className="use-case-description">
                Launch your content strategy with limited resources. 
                Get enterprise-level quality without the enterprise budget.
              </p>
            </div>
            <div className="use-case-card">
              <BarChart3 className="use-case-icon" />
              <h3 className="use-case-title">Agencies</h3>
              <p className="use-case-description">
                Deliver consistent, high-quality content to multiple clients 
                while maintaining each brand's unique voice.
              </p>
            </div>
            <div className="use-case-card">
              <Globe className="use-case-icon" />
              <h3 className="use-case-title">Businesses</h3>
              <p className="use-case-description">
                Build your content marketing engine with SEO-optimized articles, 
                social content, and email campaigns.
              </p>
            </div>
            <div className="use-case-card">
              <PlayCircle className="use-case-icon" />
              <h3 className="use-case-title">Video Creators</h3>
              <p className="use-case-description">
                Create engaging scripts that maximize retention and drive 
                subscribers across YouTube, TikTok, and more.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="container">
          <div className="cta-content">
            <h2 className="cta-title">Ready to Transform Your Content Creation?</h2>
            <p className="cta-description">
              Join creators, marketers, and businesses who are using Accordant Council 
              to produce better content faster.
            </p>
            <form className="cta-form" onSubmit={handleEmailSubmit}>
              <div className="form-group">
                <input
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="email-input"
                  required
                />
                <button type="submit" className="cta-primary form-cta">
                  Get Started Free
                  <ArrowRight className="cta-icon" />
                </button>
              </div>
            </form>
            <p className="cta-note">
              No credit card required • Start creating in seconds • Cancel anytime
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="container">
          <div className="footer-content">
            <div className="footer-brand">
              <Sparkles className="footer-logo" />
              <span className="footer-brand-name">Accordant</span>
            </div>
            <div className="footer-links">
              <a href="#how-it-works" className="footer-link">How It Works</a>
              <a href="#" className="footer-link">Documentation</a>
              <a href="#" className="footer-link">Pricing</a>
              <a href="#" className="footer-link">Contact</a>
            </div>
          </div>
          <div className="footer-bottom">
            <p className="footer-copyright">
              © 2025 Accordant LLM Council. Built with collaborative AI intelligence.
            </p>
          </div>
        </div>
      </footer>

      {/* Login Modal */}
      {showLoginModal && (
        <div className="login-modal-overlay" onClick={() => setShowLoginModal(false)}>
          <div className="login-modal-content" onClick={(e) => e.stopPropagation()}>
            <button 
              className="login-modal-close" 
              onClick={() => setShowLoginModal(false)}
              aria-label="Close login"
            >
              <X className="close-icon" />
            </button>
            <Login />
          </div>
        </div>
      )}
    </div>
  );
}

export default ContentCreatorLanding;
