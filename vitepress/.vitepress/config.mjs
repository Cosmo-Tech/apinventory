import { defineConfig } from 'vitepress'
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

// Récupère le chemin exact de CE fichier config.mjs
const __filename = fileURLToPath(import.meta.url)

// Trouve le lien exact d'un dossier en ciblant STRICTEMENT ses fichiers de propriétés
function getFolderLink(dirPath, baseDir) {
  const folderName = path.basename(dirPath)
  const parentDir = path.dirname(dirPath)

  // 1. C'est un cluster : On cherche cluster-properties.md à l'intérieur
  const clusterProp = path.join(dirPath, 'cluster-properties.md')
  if (fs.existsSync(clusterProp)) {
    let rel = path.relative(baseDir, clusterProp).replace(/\\/g, '/')
    if (rel.endsWith('.md')) rel = rel.slice(0, -3)
    return '/markdown/' + rel
  }

  // 2. C'est un tenant : On cherche le fichier tenant-xxx-properties.md au niveau du PARENT
  const siblingProp = path.join(parentDir, `${folderName}-properties.md`)
  if (fs.existsSync(siblingProp)) {
    let rel = path.relative(baseDir, siblingProp).replace(/\\/g, '/')
    if (rel.endsWith('.md')) rel = rel.slice(0, -3)
    return '/markdown/' + rel
  }

  // 3. Fallback tenant : Si le fichier de propriété a été mis à l'intérieur du dossier par erreur
  const insideProp = path.join(dirPath, `${folderName}-properties.md`)
  if (fs.existsSync(insideProp)) {
    let rel = path.relative(baseDir, insideProp).replace(/\\/g, '/')
    if (rel.endsWith('.md')) rel = rel.slice(0, -3)
    return '/markdown/' + rel
  }

  // 4. Dernier recours : on prend le premier markdown normal du dossier
  if (fs.existsSync(dirPath)) {
    const entries = fs.readdirSync(dirPath, { withFileTypes: true })
    const anyMd = entries.find(e => e.isFile() && e.name.endsWith('.md') && e.name !== 'index.md')
    if (anyMd) {
      let rel = path.relative(baseDir, path.join(dirPath, anyMd.name)).replace(/\\/g, '/')
      if (rel.endsWith('.md')) rel = rel.slice(0, -3)
      return '/markdown/' + rel
    }
  }

  return null
}

// Construit l'arbre unique de l'inventaire
function buildTree(dirPath, baseDir) {
  if (!fs.existsSync(dirPath)) return []

  const entries = fs.readdirSync(dirPath, { withFileTypes: true })
  const tree = []

  entries.sort((a, b) => a.name.localeCompare(b.name))

  for (const entry of entries) {
    if (entry.name.startsWith('.') || entry.name === 'index.md' || entry.name === 'README.md' || entry.name === '_sidebar.md') {
      continue
    }

    // On masque les propriétés pour les attacher au clic des dossiers
    if (entry.isFile() && (entry.name.endsWith('-properties.md') || entry.name === 'cluster-properties.md')) {
      continue
    }

    const fullPath = path.join(dirPath, entry.name)

    if (entry.isDirectory()) {
      const children = buildTree(fullPath, baseDir)
      const folderLink = getFolderLink(fullPath, baseDir)

      tree.push({
        text: entry.name,
        link: folderLink,
        items: children,
        isDir: true
      })
    } else if (entry.isFile() && entry.name.endsWith('.md')) {
      const fileNameWithoutExt = path.basename(entry.name, '.md')
      let rel = path.relative(baseDir, fullPath).replace(/\\/g, '/')
      if (rel.endsWith('.md')) rel = rel.slice(0, -3)

      tree.push({
        text: fileNameWithoutExt,
        link: '/markdown/' + rel,
        isDir: false
      })
    }
  }

  return tree
}

// Transforme l'arbre au format Sidebar
function mapToSidebar(tree) {
  return tree.map(node => {
    if (node.isDir) {
      return {
        text: node.text,
        link: node.link || undefined,
        collapsed: false,
        items: mapToSidebar(node.items || [])
      }
    } else {
      return {
        text: node.text,
        link: node.link
      }
    }
  })
}

// Transforme l'arbre au format Summary
function mapToSummaryMarkdown(tree, depth = 0) {
  let content = ''
  const indent = '  '.repeat(depth)

  for (const node of tree) {
    const targetLink = node.link || '/markdown/'
    content += `${indent}- [**${node.text}**](${targetLink})\n`

    if (node.isDir && node.items && node.items.length > 0) {
      content += mapToSummaryMarkdown(node.items, depth + 1)
    }
  }
  return content
}

const dataDir = path.resolve(process.cwd(), 'data')
const markdownDir = path.resolve(process.cwd(), 'data/markdown')
const indexPath = path.resolve(process.cwd(), 'data/index.md')

function updateHomePageSummary(tree) {
  if (!tree || tree.length === 0) return

  let content = `# Cosmo Tech platforms inventory\n\n`
  content += `## Summary\n\n`
  content += mapToSummaryMarkdown(tree)

  try {
    const existingContent = fs.existsSync(indexPath) ? fs.readFileSync(indexPath, 'utf-8') : ''
    if (existingContent !== content) {
      fs.writeFileSync(indexPath, content, 'utf-8')
    }
  } catch (e) {
    console.error('Error generating index.md:', e)
  }
}

// Génération initiale
const initialTree = buildTree(markdownDir, markdownDir)
updateHomePageSummary(initialTree)

const customCss = `
:root {
  --vp-nav-bg-color: #ffb039 !important;
  --vp-nav-screen-bg-color: #ffb039 !important;
  --vp-sidebar-font-size: 11px !important;
  --vp-sidebar-item-line-height: 18px !important;
  --vp-sidebar-width: 320px !important;
  --vp-font-size-base: 11px !important;
  --vp-custom-block-font-size: 11px !important;
}

#inventory-progress-banner {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  background-color: #ef4444;
  color: #000000;
  text-align: center;
  padding: 12px 16px;
  font-size: 13px;
  font-weight: 700;
  z-index: 99999;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

body.inventory-building .VPNav {
  top: 41px !important;
}
body.inventory-building .VPSidebar {
  top: calc(var(--vp-nav-height) + 41px) !important;
}

.VPNav {
  background-color: #ffb039 !important;
  border-bottom: 1px solid rgba(0, 0, 0, 0.15) !important;
}

.VPNavBarTitle,
.VPNavBarTitle *,
.title-container,
.title-container * {
  border: none !important;
  box-shadow: none !important;
}

.VPNavBarTitle::after,
.VPNavBarTitle::before,
.VPNavBar .divider,
.VPNavBar .divider::after,
.VPNavBar .divider::before {
  display: none !important;
  content: none !important;
  border: none !important;
}

.VPNavBarTitle .title {
  color: #1a1a1a !important;
  font-size: 13px !important;
  font-weight: 700 !important;
}

.VPNavBarSearchButton,
.VPNavBarSearchButton * {
  color: #1a1a1a !important;
  fill: #1a1a1a !important;
  stroke: #1a1a1a !important;
  opacity: 1 !important;
}

.VPNavBarSearchButton {
  background-color: rgba(0, 0, 0, 0.05) !important;
  border: 1px solid rgba(0, 0, 0, 0.2) !important;
  border-radius: 6px !important;
}

.VPNavBarSearchButton .search-icon,
.VPNavBarSearchButton .search-icon svg,
.VPNavBarSearchButton .search-key,
.VPNavBarSearchButton .search-keys kbd,
.VPNavBarSearchButton .search-placeholder {
  color: #1a1a1a !important;
  fill: #1a1a1a !important;
  border-color: rgba(0, 0, 0, 0.3) !important;
  background: transparent !important;
  opacity: 1 !important;
}

.VPSwitch {
  border: 1px solid rgba(0, 0, 0, 0.25) !important;
  background-color: rgba(0, 0, 0, 0.08) !important;
  border-radius: 12px !important;
}

.VPSwitch .check {
  background-color: #1a1a1a !important;
}

.VPSwitch .icon,
.VPSwitch .icon * {
  color: #ffb039 !important;
  fill: #ffb039 !important;
}

.VPSidebar, .VPSidebar * {
  font-size: 11px !important;
  line-height: 1.2 !important;
}
.VPSidebarItem .text {
  font-size: 11px !important;
}

.VPSidebarItem,
.VPSidebarItem *,
.VPSidebarGroup,
.VPSidebarGroup * {
  margin-top: 0 !important;
  margin-bottom: 0 !important;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
}

.VPSidebarItem .item,
.VPSidebarItem .link {
  min-height: 20px !important;
  height: 20px !important;
  display: flex !important;
  align-items: center !important;
}

.vp-doc,
.vp-doc p,
.vp-doc li,
.vp-doc table,
.vp-doc td,
.vp-doc th,
.vp-doc code,
.vp-doc div {
  font-size: 11px !important;
  line-height: 1.4 !important;
}

.VPLocalSearchBox .titles {
  display: flex !important;
  flex-direction: row-reverse !important;
  justify-content: flex-end !important;
  gap: 8px !important;
}
`

function getLatestMTime(dir) {
  let latest = 0
  try {
    if (!fs.existsSync(dir)) return 0

    const dirStat = fs.statSync(dir)
    latest = Math.max(latest, dirStat.mtimeMs, dirStat.ctimeMs)

    const files = fs.readdirSync(dir, { withFileTypes: true })
    for (const file of files) {
      if (file.name.startsWith('.') || file.name === 'index.md') continue

      const fullPath = path.join(dir, file.name)
      if (file.isDirectory()) {
        latest = Math.max(latest, getLatestMTime(fullPath))
      } else {
        const stat = fs.statSync(fullPath)
        latest = Math.max(latest, stat.mtimeMs, stat.ctimeMs)
      }
    }
  } catch (e) {}
  return latest
}

export default defineConfig({
  title: "Cosmo Tech platforms inventory",

  srcDir: './data',

  head: [
    ['style', { type: 'text/css' }, customCss],
    [
      'script',
      {},
      `
      (function() {
        function checkBuildingStatus() {
          fetch('/.building?t=' + Date.now(), { method: 'GET' })
            .then(res => {
              let banner = document.getElementById('inventory-progress-banner');
              if (!banner) {
                banner = document.createElement('div');
                banner.id = 'inventory-progress-banner';
                banner.innerText = "🔄 Inventory refresh is currently in progress, some pages might not work until it's finished.";
                document.body.appendChild(banner);
              }
              if (res.status === 200) {
                banner.style.display = 'block';
                document.body.classList.add('inventory-building');
              } else {
                banner.style.display = 'none';
                document.body.classList.remove('inventory-building');
              }
            })
            .catch(() => {
              let banner = document.getElementById('inventory-progress-banner');
              if (banner) {
                banner.style.display = 'none';
                document.body.classList.remove('inventory-building');
              }
            });
        }

        setInterval(checkBuildingStatus, 1500);
        document.addEventListener('DOMContentLoaded', checkBuildingStatus);
      })();
      `
    ]
  ],

  themeConfig: {
    search: {
      provider: 'local',
      options: {
        detailedView: true,
        miniSearch: {
          options: {
            extractField: (document, fieldName) => {
              if (fieldName === 'titles') {
                const pageTitle = document.id ? document.id.split('/').slice(-2, -1)[0] || '' : ''
                return [pageTitle, ...(document.titles || [])]
              }
              return document[fieldName]
            }
          },
          searchOptions: {
            prefix: true,
            fuzzy: false,
            combineWith: 'AND'
          }
        }
      }
    },
    get sidebar() {
      const tree = buildTree(markdownDir, markdownDir)
      return mapToSidebar(tree)
    }
  },

  vite: {
    server: {
      allowedHosts: [
        'inventory-platform.cosmotech.com',
        'inventory.platform.cosmotech.com'
      ]
    },
    plugins: [
      {
        name: 'inject-custom-css-build',
        transformIndexHtml(html) {
          return html.replace(
            '</head>',
            `<style>${customCss}</style></head>`
          )
        }
      },
      {
        name: 'serve-building-flag',
        configureServer(server) {
          let wasBuilding = false

          setInterval(() => {
            const latestActivity = getLatestMTime(dataDir)
            const now = Date.now()

            const isBuilding = (now - latestActivity) < 30000

            if (wasBuilding && !isBuilding) {

              // 1. Mise à jour de l'index
              const freshTree = buildTree(markdownDir, markdownDir)
              updateHomePageSummary(freshTree)

              // 2. FORCE RELOAD VITEPRESS DANS DOCKER
              // On modifie la date d'accès/modification du fichier config.mjs
              // Vite le détecte comme un changement serveur natif, détruit son cache,
              // régénère la sidebar et force le navigateur à se rafraîchir.
              try {
                const nowTime = new Date()
                fs.utimesSync(__filename, nowTime, nowTime)
                console.log("[Inventory] Inventaire terminé, cache de la config purgé.")
              } catch (e) {
                console.error("Erreur flush config:", e)
                // Fallback de sécurité
                if (server && server.ws) {
                  server.ws.send({ type: 'full-reload' })
                }
              }
            }

            wasBuilding = isBuilding
          }, 2000)

          server.middlewares.use((req, res, next) => {
            if (req.url && req.url.startsWith('/.building')) {
              if (wasBuilding) {
                res.statusCode = 200
                res.end('building')
              } else {
                res.statusCode = 404
                res.end('not building')
              }
              return
            }
            next()
          })
        }
      }
    ]
  }
})
