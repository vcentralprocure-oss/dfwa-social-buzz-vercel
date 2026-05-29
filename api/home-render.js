// Arlington Homepage - Full Layout with All Sections
// Configurable Deals Hub URL
// Set this to the deals hub destination when ready
// Options: '/dealhub' for internal route, or 'https://deals.arlington.dfwasocialbuzz.com' for subdomain
const DEALS_HUB_URL = '#'; // Currently set to Coming Soon (no broken links)
// const DEALS_HUB_URL = '/dealhub'; // Use this when internal dealhub is ready
// const DEALS_HUB_URL = 'https://deals.arlington.dfwasocialbuzz.com'; // Use this for subdomain

export default async function handler(req, res) {
  try {
    // Fetch articles from API
    const apiRes = await fetch('https://arlington.dfwasocialbuzz.com/api/articles?list=true');
    const data = await apiRes.json();
    const articles = data.success && data.articles ? data.articles : [];
    
    // Separate sponsored articles (max 3) and regular articles
    const sponsoredArticles = articles.filter(a => a.isSponsored).slice(0, 3); // Hard cap: max 3 sponsored
    const regularArticles = articles.filter(a => !a.isSponsored);
    const recentArticles = regularArticles.slice(0, 6); // Show up to 6 regular articles
    
    const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Arlington Pulse - Local News & Deals</title>
  <meta name="description" content="Your local source for Arlington news, events, deals, and community buzz.">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    
    :root {
      --primary: #FF6B35;
      --primary-dark: #e55a2b;
      --bg-dark: #1a1a2e;
      --bg-card: #16213e;
      --text: #ffffff;
      --text-muted: #a0a0a0;
      --border: #333;
      --sponsored: #FFD700;
    }
    
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      background: var(--bg-dark);
      color: var(--text);
      line-height: 1.6;
    }
    
    /* Header */
    .header {
      background: linear-gradient(135deg, #0f1629 0%, #1a1a2e 100%);
      padding: 1rem 0;
      border-bottom: 3px solid var(--primary);
      position: sticky;
      top: 0;
      z-index: 100;
    }
    
    .header-content {
      max-width: 1200px;
      margin: 0 auto;
      padding: 0 1.5rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .logo {
      font-size: 1.75rem;
      font-weight: 800;
      color: var(--primary);
      text-decoration: none;
    }
    
    .logo span {
      color: var(--text);
      font-weight: 400;
    }
    
    .nav-links {
      display: flex;
      gap: 2rem;
    }
    
    .nav-links a {
      color: var(--text-muted);
      text-decoration: none;
      font-weight: 500;
      transition: color 0.2s;
    }
    
    .nav-links a:hover {
      color: var(--primary);
    }
    
    /* Hero Section */
    .hero {
      background: linear-gradient(135deg, #0f1629 0%, #1a1a2e 50%, #16213e 100%);
      padding: 4rem 1.5rem;
      text-align: center;
    }
    
    .hero h1 {
      font-size: 3rem;
      font-weight: 800;
      margin-bottom: 1rem;
      background: linear-gradient(135deg, var(--primary) 0%, #ff8c5a 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    
    .hero p {
      font-size: 1.25rem;
      color: var(--text-muted);
      max-width: 600px;
      margin: 0 auto 2rem;
    }
    
    /* Container */
    .container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 0 1.5rem;
    }
    
    /* Section Headers */
    .section-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.5rem;
      padding-bottom: 0.75rem;
      border-bottom: 2px solid var(--border);
    }
    
    .section-title {
      font-size: 1.5rem;
      font-weight: 700;
      color: var(--text);
    }
    
    .section-link {
      color: var(--primary);
      text-decoration: none;
      font-weight: 600;
      font-size: 0.875rem;
    }
    
    /* Featured Section */
    .featured-section {
      padding: 3rem 0;
    }
    
    .featured-grid {
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 2rem;
    }
    
    @media (max-width: 768px) {
      .featured-grid {
        grid-template-columns: 1fr;
      }
    }
    
    .featured-main {
      position: relative;
      border-radius: 12px;
      overflow: hidden;
      background: var(--bg-card);
      border: 1px solid var(--border);
    }
    
    .featured-main:hover {
      border-color: var(--primary);
    }
    
    .featured-main a {
      text-decoration: none;
      color: inherit;
      display: block;
    }
    
    .featured-image {
      width: 100%;
      height: 400px;
      object-fit: cover;
    }
    
    .featured-content {
      padding: 2rem;
    }
    
    .featured-badge {
      display: inline-block;
      background: var(--primary);
      color: white;
      padding: 0.375rem 0.875rem;
      border-radius: 4px;
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      margin-bottom: 1rem;
    }
    
    .featured-badge.sponsored {
      background: var(--sponsored);
      color: #000;
    }
    
    .featured-title {
      font-size: 1.75rem;
      font-weight: 700;
      margin-bottom: 1rem;
      line-height: 1.3;
    }
    
    .featured-excerpt {
      color: var(--text-muted);
      font-size: 1rem;
      line-height: 1.6;
    }
    
    .featured-meta {
      display: flex;
      gap: 1rem;
      margin-top: 1.5rem;
      font-size: 0.875rem;
      color: var(--text-muted);
    }
    
    /* Side Articles */
    .side-articles {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }
    
    .side-article {
      background: var(--bg-card);
      border-radius: 8px;
      overflow: hidden;
      border: 1px solid var(--border);
      transition: border-color 0.2s;
    }
    
    .side-article:hover {
      border-color: var(--primary);
    }
    
    .side-article a {
      text-decoration: none;
      color: inherit;
      display: block;
    }
    
    .side-article-image {
      width: 100%;
      height: 150px;
      object-fit: cover;
    }
    
    .side-article-content {
      padding: 1rem;
    }
    
    .side-article-title {
      font-size: 1rem;
      font-weight: 600;
      margin-bottom: 0.5rem;
      line-height: 1.4;
    }
    
    .side-article-meta {
      font-size: 0.75rem;
      color: var(--text-muted);
    }
    
    /* Sponsored Section */
    .sponsored-section {
      padding: 3rem 0;
      background: linear-gradient(135deg, #1a1a2e 0%, #0f1629 100%);
      border-top: 1px solid var(--border);
      border-bottom: 1px solid var(--border);
    }
    
    .sponsored-header {
      display: flex;
      align-items: center;
      gap: 1rem;
      margin-bottom: 1.5rem;
      padding-bottom: 0.75rem;
      border-bottom: 2px solid var(--sponsored);
    }
    
    .sponsored-label {
      font-size: 1.25rem;
      font-weight: 700;
      color: var(--sponsored);
      text-transform: uppercase;
      letter-spacing: 1px;
    }
    
    .sponsored-divider {
      flex: 1;
      height: 2px;
      background: linear-gradient(90deg, var(--sponsored) 0%, transparent 100%);
    }
    
    .sponsored-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 1.5rem;
    }
    
    @media (max-width: 768px) {
      .sponsored-grid {
        grid-template-columns: 1fr;
      }
    }
    
    .sponsored-card {
      background: var(--bg-card);
      border-radius: 8px;
      overflow: hidden;
      border: 2px solid var(--sponsored);
      transition: all 0.2s;
    }
    
    .sponsored-card:hover {
      transform: translateY(-4px);
      box-shadow: 0 8px 24px rgba(255, 215, 0, 0.15);
    }
    
    .sponsored-card a {
      text-decoration: none;
      color: inherit;
      display: block;
    }
    
    .sponsored-card-image {
      width: 100%;
      height: 160px;
      object-fit: cover;
    }
    
    .sponsored-card-content {
      padding: 1.25rem;
    }
    
    .sponsored-card-title {
      font-size: 1rem;
      font-weight: 600;
      margin-bottom: 0.5rem;
      line-height: 1.4;
      color: var(--text);
    }
    
    .sponsored-card-excerpt {
      color: var(--text-muted);
      font-size: 0.875rem;
      line-height: 1.5;
      margin-bottom: 1rem;
    }
    
    .sponsored-card-meta {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.75rem;
    }
    
    .sponsored-by {
      color: var(--sponsored);
      font-weight: 600;
    }
    
    .sponsored-card-date {
      color: var(--text-muted);
    }
    
    /* Recent Articles Section */
    .recent-section {
      padding: 3rem 0;
      border-top: 1px solid var(--border);
    }
    
    .articles-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 1.5rem;
    }
    
    .article-card {
      background: var(--bg-card);
      border-radius: 8px;
      overflow: hidden;
      border: 1px solid var(--border);
      transition: all 0.2s;
    }
    
    .article-card:hover {
      border-color: var(--primary);
      transform: translateY(-2px);
    }
    
    .article-card a {
      text-decoration: none;
      color: inherit;
      display: block;
    }
    
    .article-image {
      width: 100%;
      height: 180px;
      object-fit: cover;
    }
    
    .article-content {
      padding: 1.25rem;
    }
    
    .article-title {
      font-size: 1.125rem;
      font-weight: 600;
      margin-bottom: 0.75rem;
      line-height: 1.4;
    }
    
    .article-excerpt {
      color: var(--text-muted);
      font-size: 0.875rem;
      line-height: 1.5;
      margin-bottom: 1rem;
    }
    
    .article-meta {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.75rem;
      color: var(--text-muted);
    }
    
    .sponsored-tag {
      background: var(--sponsored);
      color: #000;
      padding: 0.25rem 0.5rem;
      border-radius: 4px;
      font-weight: 600;
    }
    
    /* Subscribe Section */
    .subscribe-section {
      padding: 4rem 0;
      background: linear-gradient(135deg, #16213e 0%, #0f1629 100%);
      border-top: 1px solid var(--border);
      border-bottom: 1px solid var(--border);
    }
    
    .subscribe-content {
      text-align: center;
      max-width: 600px;
      margin: 0 auto;
    }
    
    .subscribe-title {
      font-size: 2rem;
      font-weight: 700;
      margin-bottom: 1rem;
    }
    
    .subscribe-text {
      color: var(--text-muted);
      margin-bottom: 2rem;
      font-size: 1.125rem;
    }
    
    .subscribe-form {
      display: flex;
      gap: 1rem;
      justify-content: center;
      flex-wrap: wrap;
    }
    
    .subscribe-input {
      flex: 1;
      min-width: 250px;
      padding: 1rem 1.25rem;
      border: 2px solid var(--border);
      border-radius: 8px;
      background: var(--bg-dark);
      color: var(--text);
      font-size: 1rem;
    }
    
    .subscribe-input:focus {
      outline: none;
      border-color: var(--primary);
    }
    
    .subscribe-button {
      padding: 1rem 2rem;
      background: var(--primary);
      color: white;
      border: none;
      border-radius: 8px;
      font-weight: 600;
      font-size: 1rem;
      cursor: pointer;
      transition: background 0.2s;
    }
    
    .subscribe-button:hover {
      background: var(--primary-dark);
    }
    
    /* Deals Section */
    .deals-section {
      padding: 3rem 0;
    }
    
    .deals-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
      gap: 1.5rem;
    }
    
    .deal-card {
      background: var(--bg-card);
      border-radius: 8px;
      padding: 1.5rem;
      border: 1px solid var(--border);
      text-align: center;
    }
    
    .deal-card:hover {
      border-color: var(--primary);
    }
    
    .deal-badge {
      display: inline-block;
      background: #10b981;
      color: white;
      padding: 0.25rem 0.75rem;
      border-radius: 4px;
      font-size: 0.75rem;
      font-weight: 700;
      margin-bottom: 1rem;
    }
    
    .deal-title {
      font-size: 1.125rem;
      font-weight: 600;
      margin-bottom: 0.5rem;
    }
    
    .deal-business {
      color: var(--text-muted);
      font-size: 0.875rem;
      margin-bottom: 1rem;
    }
    
    .deal-button {
      display: inline-block;
      padding: 0.75rem 1.5rem;
      background: var(--primary);
      color: white;
      text-decoration: none;
      border-radius: 6px;
      font-weight: 600;
      border: none;
      cursor: pointer;
      transition: all 0.2s;
    }
    
    .deal-button:hover {
      background: var(--primary-dark);
    }
    
    .deal-button.disabled {
      background: #444;
      color: #888;
      cursor: not-allowed;
    }
    
    .deal-button.disabled:hover {
      background: #444;
    }
    
    /* Business Section */
    .business-section {
      padding: 4rem 0;
      background: linear-gradient(135deg, #0f1629 0%, #16213e 100%);
      border-top: 1px solid var(--border);
    }
    
    .business-content {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 4rem;
      align-items: center;
    }
    
    @media (max-width: 768px) {
      .business-content {
        grid-template-columns: 1fr;
        gap: 2rem;
      }
    }
    
    .business-text h2 {
      font-size: 2rem;
      font-weight: 700;
      margin-bottom: 1rem;
    }
    
    .business-text p {
      color: var(--text-muted);
      margin-bottom: 1.5rem;
      font-size: 1.125rem;
    }
    
    .business-button {
      display: inline-block;
      padding: 1rem 2rem;
      background: var(--primary);
      color: white;
      text-decoration: none;
      border-radius: 8px;
      font-weight: 600;
    }
    
    .business-features {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1.5rem;
    }
    
    .feature-item {
      background: var(--bg-card);
      padding: 1.5rem;
      border-radius: 8px;
      border: 1px solid var(--border);
    }
    
    .feature-icon {
      font-size: 2rem;
      margin-bottom: 0.5rem;
    }
    
    .feature-title {
      font-weight: 600;
      margin-bottom: 0.25rem;
    }
    
    .feature-desc {
      font-size: 0.875rem;
      color: var(--text-muted);
    }
    
    /* Footer */
    .footer {
      background: #0a0a0a;
      padding: 3rem 0;
      border-top: 1px solid var(--border);
    }
    
    .footer-content {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 2rem;
    }
    
    .footer-logo {
      font-size: 1.5rem;
      font-weight: 800;
      color: var(--primary);
    }
    
    .footer-links {
      display: flex;
      gap: 2rem;
    }
    
    .footer-links a {
      color: var(--text-muted);
      text-decoration: none;
    }
    
    .footer-links a:hover {
      color: var(--primary);
    }
    
    /* Mobile Responsive */
    @media (max-width: 768px) {
      .hero h1 {
        font-size: 2rem;
      }
      
      .nav-links {
        display: none;
      }
      
      .articles-grid {
        grid-template-columns: 1fr;
      }
      
      .deals-grid {
        grid-template-columns: 1fr;
      }
      
      .business-features {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <!-- Header -->
  <header class="header">
    <div class="header-content">
      <a href="/" class="logo">Arlington<span>Pulse</span></a>
      <nav class="nav-links">
        <a href="/">Home</a>
        <a href="/#news">News</a>
        <a href="/#deals">Deals</a>
        <a href="/business">Business</a>
        <a href="/subscribe/">Subscribe</a>
      </nav>
    </div>
  </header>

  <!-- Hero Section -->
  <section class="hero">
    <div class="container">
      <h1>Arlington Pulse</h1>
      <p>Your local source for Arlington news, events, deals, and community buzz. From UTA to the Entertainment District, we cover the stories that matter to Arlington locals.</p>
    </div>
  </section>

  ${sponsoredArticles.length > 0 ? `
  <!-- Sponsored Section -->
  <section class="sponsored-section" id="sponsored">
    <div class="container">
      <div class="sponsored-header">
        <span class="sponsored-label">Sponsored</span>
        <div class="sponsored-divider"></div>
      </div>
      
      <div class="sponsored-grid">
        ${sponsoredArticles.map(article => `
        <article class="sponsored-card">
          <a href="/${encodeURIComponent(article.slug)}">
            ${article.heroImage ? `<img src="${escapeHtml(article.heroImage)}" alt="${escapeHtml(article.title)}" class="sponsored-card-image">` : ''}
            <div class="sponsored-card-content">
              <h3 class="sponsored-card-title">${escapeHtml(article.title)}</h3>
              <p class="sponsored-card-excerpt">${escapeHtml(article.excerpt || '').substring(0, 100)}...</p>
              <div class="sponsored-card-meta">
                <span class="sponsored-by">Sponsored${article.sponsorName ? ' by ' + escapeHtml(article.sponsorName) : ''}</span>
                <span class="sponsored-card-date">${formatDate(article.publishDate)}</span>
              </div>
            </div>
          </a>
        </article>
        `).join('')}
      </div>
    </div>
  </section>
  ` : ''}

  <!-- Recent Articles Section -->
  <section class="recent-section">
    <div class="container">
      <div class="section-header">
        <h2 class="section-title">Latest Articles</h2>
        <a href="/" class="section-link">View All Articles →</a>
      </div>
      
      <div class="articles-grid">
        ${recentArticles.map(article => `
        <article class="article-card ${article.isSponsored ? 'sponsored' : ''}">
          <a href="/${encodeURIComponent(article.slug)}">
            ${article.heroImage ? `<img src="${escapeHtml(article.heroImage)}" alt="${escapeHtml(article.title)}" class="article-image">` : ''}
            <div class="article-content">
              <h3 class="article-title">${escapeHtml(article.title)}</h3>
              <p class="article-excerpt">${escapeHtml(article.excerpt || '').substring(0, 120)}...</p>
              <div class="article-meta">
                <span>${formatDate(article.publishDate)}</span>
                ${article.isSponsored ? '<span class="sponsored-tag">Sponsored</span>' : ''}
              </div>
            </div>
          </a>
        </article>
        `).join('')}
      </div>
    </div>
  </section>

  <!-- Subscribe Section -->
  <section class="subscribe-section" id="subscribe">
    <div class="container">
      <div class="subscribe-content">
        <h2 class="subscribe-title">Stay in the Loop</h2>
        <p class="subscribe-text">Get the latest Arlington news, events, and local deals delivered straight to your inbox. No spam, just the good stuff.</p>
        
        <!-- Step 1: Email Only -->
        <form class="subscribe-form" id="subscribe-step1">
          <input type="email" id="subscribe-email" class="subscribe-input" placeholder="Enter your email address" required>
          <input type="text" id="website" name="website" style="position:absolute;left:-9999px;" tabindex="-1" autocomplete="off"> <!-- Honeypot -->
          <button type="submit" class="subscribe-button" id="step1-button">Continue</button>
        </form>
        
        <!-- Step 2: Name Collection (Hidden initially) -->
        <form class="subscribe-form" id="subscribe-step2" style="display:none;">
          <p style="margin-bottom:1rem;color:var(--text-muted);">Almost there! Please tell us your name:</p>
          <input type="text" id="subscribe-firstname" class="subscribe-input" placeholder="First name" required style="margin-bottom:0.5rem;">
          <input type="text" id="subscribe-lastname" class="subscribe-input" placeholder="Last name" style="margin-bottom:0.5rem;">
          <div style="display:flex;gap:1rem;">
            <button type="button" class="subscribe-button" style="background:#444;" onclick="showStep1()">Back</button>
            <button type="submit" class="subscribe-button" id="step2-button">Subscribe</button>
          </div>
        </form>
        
        <div id="subscribe-message" style="margin-top: 1rem; font-weight: 500;"></div>
      </div>
    </div>
  </section>
  
  <script>
    let subscriberEmail = '';
    
    function showStep1() {
      document.getElementById('subscribe-step1').style.display = 'flex';
      document.getElementById('subscribe-step2').style.display = 'none';
      document.getElementById('subscribe-message').textContent = '';
    }
    
    function showStep2() {
      document.getElementById('subscribe-step1').style.display = 'none';
      document.getElementById('subscribe-step2').style.display = 'flex';
      document.getElementById('subscribe-firstname').focus();
    }
    
    // Step 1: Validate email
    document.getElementById('subscribe-step1').addEventListener('submit', async function(e) {
      e.preventDefault();
      
      const email = document.getElementById('subscribe-email').value.trim();
      const honeypot = document.getElementById('website').value;
      const button = document.getElementById('step1-button');
      const message = document.getElementById('subscribe-message');
      
      // Basic email validation
      if (!email || !email.includes('@') || !email.includes('.')) {
        message.style.color = '#ef4444';
        message.textContent = 'Please enter a valid email address';
        return;
      }
      
      button.disabled = true;
      button.textContent = 'Checking...';
      message.textContent = '';
      
      try {
        const response = await fetch('/api/subscribe', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, step: 'email', honeypot })
        });
        
        const data = await response.json();
        
        if (data.success && data.step === 'email_valid') {
          subscriberEmail = email;
          showStep2();
        } else {
          message.style.color = '#ef4444';
          message.textContent = data.error || 'Please check your email and try again';
        }
      } catch (error) {
        message.style.color = '#ef4444';
        message.textContent = 'Network error. Please try again.';
      } finally {
        button.disabled = false;
        button.textContent = 'Continue';
      }
    });
    
    // Step 2: Complete subscription
    document.getElementById('subscribe-step2').addEventListener('submit', async function(e) {
      e.preventDefault();
      
      const firstName = document.getElementById('subscribe-firstname').value.trim();
      const lastName = document.getElementById('subscribe-lastname').value.trim();
      const button = document.getElementById('step2-button');
      const message = document.getElementById('subscribe-message');
      
      if (!firstName) {
        message.style.color = '#ef4444';
        message.textContent = 'Please enter your first name';
        return;
      }
      
      button.disabled = true;
      button.textContent = 'Subscribing...';
      message.textContent = '';
      
      try {
        const response = await fetch('/api/subscribe', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            email: subscriberEmail, 
            firstName,
            lastName,
            step: 'complete',
            source: 'arlington-homepage'
          })
        });
        
        const data = await response.json();
        
        if (data.success) {
          message.style.color = '#10b981';
          message.textContent = data.message || 'Check your email to confirm!';
          document.getElementById('subscribe-step2').style.display = 'none';
          document.getElementById('subscribe-step1').style.display = 'none';
        } else {
          message.style.color = '#ef4444';
          message.textContent = data.error || 'Subscription failed. Please try again.';
          button.disabled = false;
          button.textContent = 'Subscribe';
        }
      } catch (error) {
        message.style.color = '#ef4444';
        message.textContent = 'Network error. Please try again.';
        button.disabled = false;
        button.textContent = 'Subscribe';
      }
    });
  </script>

  <!-- Deals Section -->
  <section class="deals-section" id="deals">
    <div class="container">
      <div class="section-header">
        <h2 class="section-title">Local Deals</h2>
        ${DEALS_HUB_URL === '#' 
          ? '<span class="section-link" style="cursor:not-allowed;opacity:0.6;">View All Deals (Coming Soon) →</span>'
          : `<a href="${DEALS_HUB_URL}" class="section-link" ${DEALS_HUB_URL.startsWith('http') ? 'target="_blank" rel="noopener"' : ''}>View All Deals →</a>`
        }
      </div>
      
      <div class="deals-grid">
        ${getDeals().map(deal => `
        <div class="deal-card ${deal.isActive ? 'active' : 'inactive'}">
          <span class="deal-badge">${escapeHtml(deal.badgeText)}</span>
          <h3 class="deal-title">${escapeHtml(deal.title)}</h3>
          <p class="deal-business">${escapeHtml(deal.businessName)}</p>
          ${deal.isActive 
            ? `<a href="${escapeHtml(deal.offerUrl)}" class="deal-button" target="_blank" rel="noopener">${escapeHtml(deal.buttonText)}</a>`
            : `<button class="deal-button disabled" disabled>${escapeHtml(deal.buttonText)}</button>`
          }
        </div>
        `).join('')}
      </div>
    </div>
  </section>

  <!-- Business Section -->
  <section class="business-section" id="business">
    <div class="container">
      <div class="business-content">
        <div class="business-text">
          <h2>Get Your Business Featured</h2>
          <p>Join hundreds of local Arlington businesses reaching thousands of engaged local customers. From sponsored articles to featured placements, we help you connect with the community.</p>
          <a href="/business/featured" class="business-button">Get Featured</a>
        </div>
        <div class="business-features">
          <div class="feature-item">
            <div class="feature-icon">📰</div>
            <div class="feature-title">Sponsored Articles</div>
            <div class="feature-desc">Tell your story with custom content</div>
          </div>
          <div class="feature-item">
            <div class="feature-icon">🎯</div>
            <div class="feature-title">Featured Placements</div>
            <div class="feature-desc">Prime homepage visibility</div>
          </div>
          <div class="feature-item">
            <div class="feature-icon">📧</div>
            <div class="feature-title">Newsletter Features</div>
            <div class="feature-desc">Reach 5,000+ subscribers</div>
          </div>
          <div class="feature-item">
            <div class="feature-icon">🏷️</div>
            <div class="feature-title">Deal Promotions</div>
            <div class="feature-desc">Drive foot traffic with offers</div>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- Footer -->
  <footer class="footer">
    <div class="container">
      <div class="footer-content">
        <div class="footer-logo">Arlington Pulse</div>
        <div class="footer-links">
          <a href="/">Home</a>
          <a href="/about">About</a>
          <a href="/contact">Contact</a>
          <a href="/privacy">Privacy</a>
        </div>
      </div>
    </div>
  </footer>
</body>
</html>`;

    res.setHeader('Content-Type', 'text/html');
    res.status(200).send(html);
    
  } catch (error) {
    res.status(500).send(`Error: ${error.message}`);
  }
}

function escapeHtml(text) {
  if (!text) return '';
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function formatDate(dateString) {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric'
  });
}

// Editable deals data - can be moved to database/CMS later
function getDeals() {
  return [
    {
      title: "Buy One Get One Free",
      businessName: "Arlington Coffee House",
      badgeText: "50% OFF",
      buttonText: "Coming Soon",
      offerUrl: "",
      isActive: false
    },
    {
      title: "$10 Off First Order",
      businessName: "Local Eats Delivery",
      badgeText: "$10 OFF",
      buttonText: "Coming Soon",
      offerUrl: "",
      isActive: false
    },
    {
      title: "Free Consultation",
      businessName: "Arlington Wellness Center",
      badgeText: "FREE",
      buttonText: "Coming Soon",
      offerUrl: "",
      isActive: false
    },
    {
      title: "25% Off Services",
      businessName: "Downtown Auto Repair",
      badgeText: "25% OFF",
      buttonText: "Coming Soon",
      offerUrl: "",
      isActive: false
    }
  ];
}
