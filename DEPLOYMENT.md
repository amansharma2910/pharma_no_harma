# 🚀 Deployment Guide - GitHub Pages

This guide explains how to deploy the PharmaNoHarma landing page to GitHub Pages.

## 📋 Prerequisites

- GitHub account
- PharmaNoHarma repository on GitHub
- Basic knowledge of Git

## 🛠️ GitHub Pages Setup

### Step 1: Repository Configuration

1. **Navigate to your repository** on GitHub
2. **Go to Settings** → **Pages** (in the sidebar)
3. **Configure Source**:
   - Source: `Deploy from a branch`
   - Branch: `main` (or your primary branch)
   - Folder: `/ (root)`

### Step 2: Enable GitHub Pages

1. **Save the configuration**
2. **Wait 2-5 minutes** for GitHub to build and deploy
3. **Access your site** at: `https://yourusername.github.io/pharma_no_harma`

## 📁 File Structure for GitHub Pages

The repository contains these files for GitHub Pages deployment:

```
pharma_no_harma/
├── index.html              # Main landing page (HTML)
├── _config.yml             # GitHub Pages configuration
├── README.md               # Enhanced project documentation
└── DEPLOYMENT.md           # This deployment guide
```

## 🎯 Deployment Options

### Option 1: HTML Landing Page (Recommended)
- **File**: `index.html`
- **Advantages**: 
  - Custom styling and animations
  - Professional appearance
  - Fast loading
  - Full control over design
- **URL**: `https://yourusername.github.io/pharma_no_harma`

### Option 2: Markdown README as Landing Page
- **File**: `README.md`
- **Advantages**:
  - Easy to edit
  - GitHub-native rendering
  - Automatic formatting
- **URL**: `https://yourusername.github.io/pharma_no_harma` (falls back to README if no index.html)

## ⚙️ Customization

### Update GitHub URLs

Before deploying, replace these placeholders in the files:

**In `index.html`:**
```html
<!-- Replace "yourusername" with your actual GitHub username -->
<a href="https://github.com/yourusername/pharma_no_harma">GitHub</a>
```

**In `_config.yml`:**
```yaml
# Replace with your actual details
url: "https://yourusername.github.io"
baseurl: "/pharma_no_harma"
github_username: "yourusername"
email: "your-email@example.com"
```

**In `README.md`:**
```markdown
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Live-brightgreen)](https://yourusername.github.io/pharma_no_harma)
```

### Customize Content

1. **Update project details** in `index.html`
2. **Modify contact information**
3. **Add screenshots or demo videos**
4. **Update technology stack** if needed

## 🔧 Advanced Configuration

### Custom Domain (Optional)

1. **Create a `CNAME` file** in the repository root:
   ```
   yourdomain.com
   ```

2. **Update DNS records** for your domain:
   - Add a CNAME record pointing to `yourusername.github.io`

3. **Configure in GitHub**:
   - Go to Settings → Pages
   - Enter your custom domain
   - Enable "Enforce HTTPS"

### Jekyll Theme Customization

If you want to use Jekyll themes with the markdown approach:

1. **Update `_config.yml`**:
   ```yaml
   theme: minima  # or any supported theme
   plugins:
     - jekyll-feed
     - jekyll-sitemap
   ```

2. **Create custom layouts** in `_layouts/` directory

3. **Add custom CSS** in `assets/css/` directory

## 🚦 Testing Deployment

### Local Testing

1. **Install Jekyll** (optional):
   ```bash
   gem install bundler jekyll
   ```

2. **Create Gemfile**:
   ```ruby
   source "https://rubygems.org"
   gem "github-pages", group: :jekyll_plugins
   ```

3. **Run locally**:
   ```bash
   bundle install
   bundle exec jekyll serve
   ```

4. **Visit**: `http://localhost:4000`

### Live Testing

1. **Push changes** to GitHub
2. **Wait for deployment** (check Actions tab)
3. **Test the live site**
4. **Check for broken links**

## ⚡ Quick Deployment Checklist

- [ ] Replace all `yourusername` placeholders
- [ ] Update contact information
- [ ] Test all links
- [ ] Verify GitHub Pages is enabled
- [ ] Check that the site builds successfully
- [ ] Test on mobile devices
- [ ] Verify all sections display correctly

## 🐛 Troubleshooting

### Common Issues

**Site not loading:**
- Check GitHub Pages settings
- Ensure `index.html` exists in the root
- Wait 5-10 minutes after enabling Pages

**404 Error:**
- Verify the repository is public
- Check the branch settings in Pages configuration
- Ensure file names are correct

**Styling not working:**
- Check CSS file paths
- Verify all assets are in the repository
- Use relative paths, not absolute ones

**Content not updating:**
- Clear browser cache
- Check GitHub Actions for build errors
- Wait for GitHub's CDN to update

### Build Errors

1. **Check the Actions tab** in your repository
2. **Look for build logs** and error messages
3. **Common fixes**:
   - Fix syntax errors in `_config.yml`
   - Ensure all files are committed
   - Check file permissions

## 📞 Support

If you encounter issues:

1. **Check GitHub Pages documentation**: https://docs.github.com/en/pages
2. **Review GitHub Actions logs** for error details
3. **Open an issue** in the repository
4. **Contact the development team**

## 🎉 Success!

Once deployed, your PharmaNoHarma landing page will be live at:
- **Primary URL**: `https://yourusername.github.io/pharma_no_harma`
- **Custom Domain**: `https://yourdomain.com` (if configured)

The landing page will automatically update when you push changes to the main branch!

---

**Built with ❤️ for accessible healthcare** 