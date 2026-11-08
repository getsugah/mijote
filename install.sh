#!/usr/bin/env bash
# Installation depuis les sources ; aucune installation de paquet système.
set -Eeuo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
fail() { printf 'Erreur : %s\n' "$*" >&2; exit 1; }
trap 'printf "Échec à la ligne %s. Les données sont conservées.\n" "$LINENO" >&2' ERR
mode=${1:-install}
case "$mode" in
  install|update|uninstall) ;;
  --help|-h) printf 'Usage : bash install.sh [install|update|uninstall]\n'; exit 0 ;;
  *) fail 'Mode inconnu. Utiliser install, update ou uninstall.' ;;
esac
for tool in docker git; do
  command -v "$tool" >/dev/null || fail "$tool manque. Installez-le avec la documentation de votre serveur, puis relancez ce script."
done
version=$(docker compose version --short) || fail 'Docker Compose v2 manque. Installez le plugin Compose v2.'
[[ $version == 2.* || $version == v2.* ]] || fail 'Docker Compose v2 est nécessaire.'
docker info >/dev/null 2>&1 || fail 'Docker Engine est arrêté ou inaccessible. Vérifiez le service et les permissions Docker ; si nécessaire, relancez avec sudo bash install.sh (même mode).'
[[ -f compose.yaml && -f Dockerfile && -f .env.example ]] || fail 'Sources incomplètes : lancez le script depuis un clone complet.'
# Les variables du terminal ne doivent pas remplacer silencieusement le .env.
compose() {
  env -u MIJOTE_BIND -u MIJOTE_PORT -u MIJOTE_ALLOWED_ORIGINS -u MIJOTE_SECURE_COOKIE \
      -u COMPOSE_FILE -u COMPOSE_PROJECT_NAME -u COMPOSE_PROFILES -u COMPOSE_ENV_FILES \
      docker compose --project-name mijote --file compose.yaml --env-file .env "$@"
}
ask() {
  local answer
  read -r -p "$1 [$2] : " answer || fail 'Saisie interrompue.'
  REPLY=${answer:-$2}
}
private_ipv4() {
  local a b c d extra
  IFS=. read -r a b c d extra <<< "$1"
  [[ -z ${extra:-} && $a =~ ^[0-9]{1,3}$ && $b =~ ^[0-9]{1,3}$ && $c =~ ^[0-9]{1,3}$ && $d =~ ^[0-9]{1,3}$ ]] || return 1
  a=$((10#$a)); b=$((10#$b)); c=$((10#$c)); d=$((10#$d))
  (( a <= 255 && b <= 255 && c <= 255 && d <= 255 )) || return 1
  (( a == 10 || a == 127 || (a == 172 && b >= 16 && b <= 31) || (a == 192 && b == 168) ))
}
if [[ $mode == uninstall ]]; then
  [[ -f .env ]] || fail 'Aucun .env trouvé : impossible d’identifier la configuration à désinstaller.'
  printf 'Les conteneurs et le réseau Compose Mijote seront supprimés. Le volume, les sources, les images et le .env seront conservés.\n'
  ask 'Tapez DESINSTALLER pour confirmer' 'non'
  [[ $REPLY == DESINSTALLER ]] || { printf 'Annulé.\n'; exit 0; }
  compose down
  printf 'Désinstallation terminée. Données conservées ; bash install.sh permet de réinstaller.\n'
  exit 0
fi
if [[ $mode == update ]]; then
  [[ -f .env ]] || fail 'Installez d’abord avec bash install.sh.'
  [[ -d .git || -f .git ]] || fail 'La mise à jour automatique nécessite un clone Git.'
  [[ -z $(git status --porcelain --untracked-files=normal) ]] || fail 'Modifications locales détectées. Conservez-les ou commitez-les avant la mise à jour ; aucun fichier ne sera écrasé.'
  branch=$(git symbolic-ref --quiet --short HEAD) || fail 'Revenez sur une branche Git avant la mise à jour.'
  upstream=$(git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null || true)
  if [[ -n $upstream ]]; then
    remote=$(git config --get "branch.$branch.remote")
    ref=$(git config --get "branch.$branch.merge")
  else
    remote=origin
    ref="refs/heads/$branch"
  fi
  [[ $remote != . ]] || fail 'La branche suivie doit appartenir à un dépôt distant.'
  printf 'Sauvegardez la base avant toute mise à jour (voir README).\n'
  ask "Mettre à jour depuis $remote, branche ${ref#refs/heads/} ? Tapez OUI" 'non'
  [[ $REPLY == OUI ]] || { printf 'Annulé.\n'; exit 0; }
  git fetch "$remote" "$ref"
  git merge --ff-only FETCH_HEAD || fail 'Historique divergent : aucune fusion automatique. Résolvez la situation Git manuellement.'
fi
if [[ ! -e .env ]]; then
  printf 'HTTP doit rester limité à un réseau privé de confiance. Aucun port du routeur ou du pare-feu ne sera ouvert.\n'
  ask 'Port HTTP' '8095'; port=$REPLY
  [[ $port =~ ^[0-9]{1,5}$ ]] && (( 10#$port >= 1 && 10#$port <= 65535 )) || fail 'Port invalide (1 à 65535).'
  port=$((10#$port))
  ask 'Adresse IPv4 d’écoute (0.0.0.0 pour le réseau local)' '0.0.0.0'; bind=$REPLY
  [[ $bind == 0.0.0.0 ]] || private_ipv4 "$bind" || fail 'Utilisez une IPv4 privée, de boucle locale ou 0.0.0.0.'
  detected=''
  if command -v ip >/dev/null; then
    detected=$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src") {print $(i+1); exit}}' || true)
  fi
  if [[ $bind != 0.0.0.0 ]]; then detected=$bind; fi
  private_ipv4 "$detected" || detected=''
  ask 'IPv4 privée du serveur utilisée par le navigateur' "$detected"; host=$REPLY
  private_ipv4 "$host" || fail 'Une IPv4 privée ou de boucle locale est nécessaire ; ne renseignez pas une adresse publique.'
  if [[ $bind != 0.0.0.0 && $host != "$bind" ]]; then fail 'L’adresse du navigateur doit correspondre à l’adresse d’écoute choisie.'; fi
  (umask 077; set -o noclobber; cat > .env <<ENV
MIJOTE_BIND=$bind
MIJOTE_PORT=$port
MIJOTE_ALLOWED_ORIGINS=http://$host:$port,http://localhost:$port,http://127.0.0.1:$port
MIJOTE_SECURE_COOKIE=false
ENV
  ) || fail 'Création de .env impossible ; aucun fichier existant n’a été remplacé.'
else
  printf 'Configuration .env existante conservée sans modification.\n'
fi
compose config --quiet || fail 'Configuration Compose invalide. Vérifiez .env.'
resolved=$(compose config --environment)
value() { printf '%s\n' "$resolved" | sed -n "s/^$1=//p"; }
port=$(value MIJOTE_PORT); port=${port:-8080}
bind=$(value MIJOTE_BIND); bind=${bind:-127.0.0.1}
origins=$(value MIJOTE_ALLOWED_ORIGINS); origins=${origins:-http://localhost:8080}
container=$(compose ps --all --quiet mijote)
# Une relance peut réutiliser le port déjà publié par son propre conteneur.
running=false
if [[ -n $container ]]; then running=$(docker inspect --format '{{.State.Running}}' "$container"); fi
if [[ $running != true ]] && command -v ss >/dev/null; then
  occupied=$(ss -H -ltn "sport = :$port")
  [[ -z $occupied ]] || fail "Le port $port est déjà occupé. Choisissez un autre port dans .env et adaptez MIJOTE_ALLOWED_ORIGINS."
fi
printf 'Construction de l’image (le premier lancement peut prendre plusieurs minutes)…\n'
compose build || fail 'Construction impossible. Vérifiez la connexion réseau, l’espace disque et les messages Docker.'
compose up -d || fail "Démarrage impossible. Vérifiez les permissions, le port $port et les messages Docker. Les données sont conservées."
container=$(compose ps --all --quiet mijote)
[[ -n $container ]] || fail 'Conteneur Mijote introuvable après démarrage.'
for ((attempt=0; attempt<90; attempt++)); do
  state=$(docker inspect --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}' "$container")
  case "$state" in
    'running healthy')
      printf 'Mijote est sain. Adresse(s) autorisée(s) : %s\n' "$origins"
      printf 'Ouvrez l’adresse correspondant à votre serveur. Au premier lancement, créez votre compte familial.\n'
      exit 0 ;;
    *unhealthy*|exited*|dead*) break ;;
  esac
  sleep 2
done
fail 'Le conteneur n’est pas devenu sain. Consultez docker compose logs --tail=50 mijote. Aucune donnée n’a été supprimée.'
