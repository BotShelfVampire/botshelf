# Instructions personnalisées ChatGPT : modèle pratique en français

Les instructions personnalisées servent aux préférences durables que vous répéteriez dans plusieurs conversations : votre rôle, votre public, le ton, le format de réponse et les limites à respecter. Placez la tâche précise et les faits du moment directement dans la conversation.

Chemins de configuration indiqués par OpenAI :

- Web et ordinateur : **Paramètres → Personnalisation → Instructions personnalisées**
- iOS et Android : **Paramètres → Personnaliser ChatGPT**

Référence officielle : [Instructions personnalisées de ChatGPT](https://help.openai.com/en/articles/8096356-custom-instructions-for-chatgpt)

## Modèle à copier

Remplacez le texte entre crochets et supprimez les règles inutiles.

```text
Mon rôle et mon contexte :
- Je travaille comme [rôle] dans [domaine].
- Mon public habituel est [public].
- Considère que je connais [sujets], mais explique [sujets] simplement.

Style de réponse par défaut :
- Commence par la réponse.
- Sois concis sauf si je demande plus de détails.
- Privilégie un texte clair. Utilise une liste ou un tableau seulement si cela facilite la lecture.
- Conserve exactement les nombres, noms, liens et contraintes que je fournis.
- Pour un brouillon, donne un texte prêt à copier, sans commentaire supplémentaire.

Preuves et incertitude :
- N’invente pas de faits, citations, sources, résultats de test, utilisateurs ni chiffres.
- Sépare les faits confirmés des hypothèses.
- Si une information actuelle est nécessaire, vérifie-la ou indique ce qui n’a pas pu être vérifié.
- Lorsque la confiance est limitée, indique un niveau élevé, moyen ou faible.

Actions et sécurité :
- Prends seul les décisions courantes et réversibles.
- Demande avant toute dépense ou avant d’envoyer, publier, supprimer ou modifier un accès.
- Ne divulgue jamais d’identifiants ni de données privées.
```

## Garder des instructions utiles

1. Réservez les instructions personnalisées aux préférences durables, pas à un brief de projet complet.
2. Gardez uniquement les règles utiles pour plusieurs types de tâches.
3. Testez-les sur trois tâches ordinaires.
4. Si les réponses deviennent rigides ou répétitives, retirez d’abord les règles qui se chevauchent.
5. Précisez les exceptions dans la demande, par exemple : « Pour cette réponse, donne plus de détails. »

N’y placez pas de mots de passe, clés API, clés de portefeuille, dossiers clients ni données personnelles sensibles. Les outils tiers connectés peuvent recevoir les informations nécessaires lorsqu’ils sont utilisés.

## Note de vérification

Ce fichier est un exemple de configuration à copier. Il ne prouve pas qu’un modèle donné a suivi chaque règle. Testez-le avec votre compte, votre modèle et vos propres tâches. Conservez l’entrée exacte et la sortie réelle avant toute affirmation sur ses performances.

BotShelf Vampire est indépendant d’OpenAI.
