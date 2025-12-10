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
import Logo from "./Logo";
import "./AccordantLanding.css";


function AccordantLanding({ onShowLogin }) {
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
    <div className="accordant-landing">
      {/* Header Navigation */}
      <header className="landing-header">
        <div className="container">
          <div className="header-content">
            <div className="header-brand">
              <Logo size="md" />
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
              Get Better Answers Through
              <span className="gradient-text"> Collaborative AI Intelligence</span>
            </h1>
            <p className="hero-description">
              Accordant AI Council brings together multiple specialized AI personalities
              that collaborate, debate, and synthesize the best possible answer to your questions.
              Get multiple perspectives, peer-reviewed quality, and comprehensive solutions for any challenge.
            </p>
            <div className="hero-cta-group">
              <button className="cta-primary" onClick={handleGetStarted}>
                Get Started Free
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
                Your query goes to multiple specialized AI personalities simultaneously.
                Each provides their unique perspective—from creative thinking to analytical rigor,
                strategic planning to tactical execution.
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
                high-quality answer that combines the best insights from every approach.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Content Types Section */}
      <section id="content-types" className="content-types-section">
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">Versatile AI Council Capabilities</h2>
            <p className="section-subtitle">
              From strategic planning to creative execution, your Accordant Council adapts to tackle
              any challenge across industries and use cases.
            </p>
          </div>
          <div className="content-types-grid">
            <div className="content-type-card">
              <div className="card-icon-wrapper">
                <FileText className="card-icon" />
              </div>
              <h3 className="card-title">Strategic Planning</h3>
              <p className="card-description">
                Comprehensive analysis, strategic frameworks, and actionable plans that consider
                multiple perspectives and potential outcomes.
              </p>
              <ul className="card-features">
                <li><CheckCircle2 className="feature-icon" /> Multi-faceted analysis</li>
                <li><CheckCircle2 className="feature-icon" /> Risk assessment</li>
                <li><CheckCircle2 className="feature-icon" /> Actionable recommendations</li>
              </ul>
            </div>
            <div className="content-type-card">
              <div className="card-icon-wrapper">
                <Video className="card-icon" />
              </div>
              <h3 className="card-title">Creative Solutions</h3>
              <p className="card-description">
                Innovative ideas, creative approaches, and out-of-the-box thinking that combines
                imagination with practical execution.
              </p>
              <ul className="card-features">
                <li><CheckCircle2 className="feature-icon" /> Creative ideation</li>
                <li><CheckCircle2 className="feature-icon" /> Multiple concepts</li>
                <li><CheckCircle2 className="feature-icon" /> Feasibility analysis</li>
              </ul>
            </div>
            <div className="content-type-card">
              <div className="card-icon-wrapper">
                <Share2 className="card-icon" />
              </div>
              <h3 className="card-title">Problem Solving</h3>
              <p className="card-description">
                Complex problem decomposition, root cause analysis, and systematic solutions
                that address challenges from multiple angles.
              </p>
              <ul className="card-features">
                <li><CheckCircle2 className="feature-icon" /> Root cause analysis</li>
                <li><CheckCircle2 className="feature-icon" /> Solution evaluation</li>
                <li><CheckCircle2 className="feature-icon" /> Implementation planning</li>
              </ul>
            </div>
            <div className="content-type-card">
              <div className="card-icon-wrapper">
                <Mail className="card-icon" />
              </div>
              <h3 className="card-title">Technical Analysis</h3>
              <p className="card-description">
                Deep technical insights, code reviews, architecture recommendations, and
                implementation strategies backed by multiple expert perspectives.
              </p>
              <ul className="card-features">
                <li><CheckCircle2 className="feature-icon" /> Code quality review</li>
                <li><CheckCircle2 className="feature-icon" /> Architecture patterns</li>
                <li><CheckCircle2 className="feature-icon" /> Best practices</li>
              </ul>
            </div>
            <div className="content-type-card">
              <div className="card-icon-wrapper">
                <Layers className="card-icon" />
              </div>
              <h3 className="card-title">Research & Analysis</h3>
              <p className="card-description">
                Comprehensive research synthesis, data analysis, and evidence-based insights
                that combine multiple sources and methodologies.
              </p>
              <ul className="card-features">
                <li><CheckCircle2 className="feature-icon" /> Multi-source synthesis</li>
                <li><CheckCircle2 className="feature-icon" /> Data interpretation</li>
                <li><CheckCircle2 className="feature-icon" /> Evidence evaluation</li>
              </ul>
            </div>
            <div className="content-type-card">
              <div className="card-icon-wrapper">
                <Search className="card-icon" />
              </div>
              <h3 className="card-title">Decision Support</h3>
              <p className="card-description">
                Informed decision-making with pros/cons analysis, scenario planning, and
                recommendations that consider multiple factors and stakeholders.
              </p>
              <ul className="card-features">
                <li><CheckCircle2 className="feature-icon" /> Pros/cons analysis</li>
                <li><CheckCircle2 className="feature-icon" /> Scenario planning</li>
                <li><CheckCircle2 className="feature-icon" /> Stakeholder considerations</li>
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
                      Each AI personality brings unique expertise—creative thinking, analytical rigor,
                      strategic planning, tactical execution, and more.
                    </p>
                  </div>
                </div>
                <div className="benefit-item">
                  <Shield className="benefit-icon" />
                  <div className="benefit-content">
                    <h3 className="benefit-title">Quality Assurance</h3>
                    <p className="benefit-description">
                      Peer review process catches errors, identifies gaps, and ensures
                      your answers meet the highest standards of accuracy and completeness.
                    </p>
                  </div>
                </div>
                <div className="benefit-item">
                  <BarChart3 className="benefit-icon" />
                  <div className="benefit-content">
                    <h3 className="benefit-title">Optimized for Results</h3>
                    <p className="benefit-description">
                      Solutions are crafted with practical applicability, effectiveness, and
                      real-world impact in mind from the start.
                    </p>
                  </div>
                </div>
                <div className="benefit-item">
                  <Globe className="benefit-icon" />
                  <div className="benefit-content">
                    <h3 className="benefit-title">Versatile Application</h3>
                    <p className="benefit-description">
                      Adapt solutions across contexts and domains while maintaining consistency
                      and applying domain-specific best practices.
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
                    <div className="message-author">Creative Thinker</div>
                    <div className="message-text">"Let's explore innovative approaches..."</div>
                  </div>
                  <div className="visual-message">
                    <div className="message-author">Analytical Strategist</div>
                    <div className="message-text">"We need to consider the data..."</div>
                  </div>
                  <div className="visual-message">
                    <div className="message-author">Practical Operator</div>
                    <div className="message-text">"Let's focus on implementation..."</div>
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
              Whether you're working solo or as part of a team, Accordant scales with your needs.
            </p>
          </div>
          <div className="use-cases-grid">
            <div className="use-case-card">
              <PenTool className="use-case-icon" />
              <h3 className="use-case-title">Knowledge Workers</h3>
              <p className="use-case-description">
                Get comprehensive answers to complex questions without sacrificing quality.
                Leverage multiple AI perspectives on every challenge.
              </p>
            </div>
            <div className="use-case-card">
              <TrendingUp className="use-case-icon" />
              <h3 className="use-case-title">Business Teams</h3>
              <p className="use-case-description">
                Make informed decisions with comprehensive analysis and multiple perspectives
                while maintaining strategic consistency.
              </p>
            </div>
            <div className="use-case-card">
              <Rocket className="use-case-icon" />
              <h3 className="use-case-title">Startups</h3>
              <p className="use-case-description">
                Make strategic decisions with limited resources.
                Get enterprise-level analysis without the enterprise budget.
              </p>
            </div>
            <div className="use-case-card">
              <BarChart3 className="use-case-icon" />
              <h3 className="use-case-title">Consultants</h3>
              <p className="use-case-description">
                Deliver consistent, high-quality analysis and recommendations to multiple clients
                while maintaining each client's unique context and requirements.
              </p>
            </div>
            <div className="use-case-card">
              <Globe className="use-case-icon" />
              <h3 className="use-case-title">Enterprises</h3>
              <p className="use-case-description">
                Enhance decision-making processes with comprehensive analysis,
                strategic planning, and multi-perspective problem-solving.
              </p>
            </div>
            <div className="use-case-card">
              <PlayCircle className="use-case-icon" />
              <h3 className="use-case-title">Researchers</h3>
              <p className="use-case-description">
                Synthesize complex information, evaluate multiple sources, and develop
                comprehensive insights across diverse domains.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="container">
          <div className="cta-content">
            <h2 className="cta-title">Ready to Get Better Answers?</h2>
            <p className="cta-description">
              Join professionals, teams, and organizations who are using Accordant Council
              to make better decisions and solve complex challenges.
            </p>
            <form className="cta-form" onSubmit={handleEmailSubmit}>
              <div className="form-group">
                <input
                  id="landing-email"
                  name="email"
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
              No credit card required • Start using in seconds • Cancel anytime
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="container">
          <div className="footer-content">
            <div className="footer-brand">
              <Logo size="md" />
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

export default AccordantLanding;
