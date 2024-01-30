# Bash-Bookmarks
[![GitHub license](https://img.shields.io/github/license/ArtBIT/bash-bookmarks.svg)](https://github.com/ArtBIT/bash-bookmarks) [![GitHub stars](https://img.shields.io/github/stars/ArtBIT/bash-bookmarks.svg)](https://github.com/ArtBIT/bash-bookmarks)  [![awesomeness](https://img.shields.io/badge/awesomeness-maximum-red.svg)](https://github.com/ArtBIT/bash-bookmarks)

CLI-first plain-text bookmarks manager.

# Purpose

Over the years I've accumulated over 10k bookmarks in Pocket. Navigating that amount of items is slow, and incredibly hard to maintain. Being a CLI-first person, I've decided to create a simple bookmarks manager that will allow me to quickly search and open bookmarks from the terminal.

To make it work, I've created a custom protocol handler for `bookmarks://...` uri scheme, and a bookmaklet that will allow me to quickly add bookmarks to the database from the browser. I've later made a [Firefox Add-On](https://github.com/ArtBIT/bash-bookmarks-firefox-add-on) to make things even more seamless.

A really handy feature of bash-bookmarks is the ability to bookmark local files or filepaths. This is especially useful when you have a lot of projects and you want to quickly navigate to a specific file.

For an example, I have a bookmark called `bash-bookmarks` which points to the `README.md` file in this repository. To open that file, I simply type `be bash-bookmarks` in the terminal and the file will open in my default editor.

```
ba --uri ../bash-bookmarks/README.md --title "bash-bookmarks"

# opens the URI using the system handler
bo bash-bookmarks
```

# Usage

```
# Bookmark Documents folder
cd ~/Documents
ba .

# Bookmark project folder
cd ~/code/github/bash-bookmarks
ba .

# quickly cd into ~/Documents
b Doc

# come back to bash-bookmarks
b bash-b

```

# Import

You can export your browser bookmarks to a [bookmarks HTML file](https://learn.microsoft.com/en-us/previous-versions/windows/internet-explorer/ie-developer/platform-apis/aa753582%28v%3Dvs.85%29) and then import the bookmarks to bash-bookmarks.

```
b import bookmarks.html
```

# Configuration

You can create an `.env` file in `$HOME/.bookmarks.env` where you can specify your prefered configuration:

```
# Specify the directory where you want to store your bookmarks
BOOKMARKS_DIR="${HOME}/bookmarks"

# Specify the editor that you want to use to edit your bookmarks
MARKDOWN_EDITOR="vim"

# Specify the viewer that you want to use to view your bookmarks
MARKDOWN_VIEWER="glow"

# Specify the browser that you want to use to open your bookmarks
BOOKMARKS_BROWSER="firefox-nightly"
```

You can have multiple `.env` files and pass the one that you want to use via the `--env` param:

```
b --env ~/bookmarks-work.env
```

```
b --env ~/bookmarks-local.env
```



# Tips:

Be sure to source the `.bookmarksrc` file in your `.bashrc` or `.zshrc` file. This will define some handy aliases and functions.

To quickly bookmark the current directory by typing `ba .` or `ba $(pwd)`.

You can export your Pinterest pins to a bookmarks.html file using a script like [PinBack](https://github.com/pinbackit/pinback), and then import it to bash-bookmarks.



# Demo

[![asciicast](https://asciinema.org/a/czTpD0PD9kA620X49oaj3iYbt.svg)](https://asciinema.org/a/czTpD0PD9kA620X49oaj3iYbt)

# Dependencies

- [fzf](https://github.com/junegunn/fzf)
- [glow](https://github.com/charmbracelet/glow)
- [fd](https://github.com/sharkdp/fd)

# Installation

Let's create a `bookmarks://...` protocol handler in Ubuntu as an example

1. First we create a bookmarks launcher script which will handle `bookmarks://...` uri.

We already have that in [./bookmarks-uri-handler](./bookmarks-uri-handler) file.

2. Next, we register the gnome `.desktop` app

We do that by simply copying [./bookmarks.desktop](./bookmarks.desktop) file to one of these locations:

 - `/usr/share/applications/bookmarks.desktop` or
 - `$HOME/.local/share/applications/bookmarks.desktop`

3. Refresh mime types database

In the `.dektop` file, the line `MimeType=x-scheme-handler/bookmarks` registers `bookmarks://` scheme handler, but to make it work we should update the mime types database cache. 

To do that, we run these commands:

```
sudo update-desktop-database
```

If that does not work, we manually register the handler:

```
xdg-mime default bookmarks.desktop x-scheme-handler/bookmarks
```

4. Test

Now everything should work. To test that it works from terminal, launch this command:

```
xdg-open 'bookmarks://?title=Test&uri=https%3A%2F%2Fgoogle.com&category=search&tags=[]'
```

This should add a new bookmark to the bookmarks directory.

5. Configure `bookmarks://` protocol handler in Firefox 

Go to `about:config`

Search for `network.protocol-handler.expose.bookmarks`

Select `boolean`, add it, and set it to `false`. 

Firefox should now delegate this protocol handler to the system handler.

6. Configure `bookmarks://` protocol handler in Chrome

Go to `chrome://settings/handlers`

Search for `bookmarks`

Select `bookmarks://` protocol handler and set it to `Always allow`

# Bookmarklet

To add a bookmarklet to your browser, simply create a new bookmark and paste the following code into the URL field:

```
javascript:(function()%7Bfunction%20d(a%2Cc%2Cg)%7Bvar%20e%3Ddocument.createElement(a)%2Cb%3Bfor(b%20in%20c)if(%22style%22%3D%3Db)for(var%20f%20in%20c%5Bb%5D)0%3D%3Df.indexOf(%22--%22)%3Fe.style.setProperty(f%2Cc%5Bb%5D%5Bf%5D)%3Ae.style%5Bf%5D%3Dc%5Bb%5D%5Bf%5D%3Belse%20if(%22events%22%3D%3Db)for(var%20h%20in%20c%5Bb%5D)e.addEventListener(h%2Cc%5Bb%5D%5Bh%5D)%3Belse%22innerHTML%22%3D%3Db%3Fe.innerHTML%3Dc%5Bb%5D%3A!0%3D%3D%3Dc%5Bb%5D%7C%7C!1%3D%3D%3Dc%5Bb%5D%3Fc%5Bb%5D%26%26e.setAttribute(b%2C%22%22)%3Ae.setAttribute(b%2Cc%5Bb%5D)%3Bg%26%26g.forEach(function(n)%7Breturn%20n%26%26e.appendChild(n)%7D)%3Breturn%20e%7Dfunction%20m()%7BsetTimeout(function()%7Bdocument.addEventListener(%22keydown%22%2Cp)%3Bdocument.body.removeChild(q)%7D%2C1E3)%7Dfunction%20k(a)%7Bvar%20c%3Da.name%2Cg%3Da.label%2Ce%3Da.value%2Cb%3Da.placeholder%2Cf%3Dvoid%200%3D%3D%3Da.type%3F%22text%22%3Aa.type%2Ch%3Dvoid%200%3D%3D%3Da.required%3F!1%3Aa.required%3Ba%3Dvoid%200%3D%3D%3Da.hidden%3F!1%3Aa.hidden%3Breturn%20d(%22div%22%2C%7B%7D%2C%5Ba%26%26d(%22label%22%2C%7B%22for%22%3Ac%2CinnerHTML%3Ag%7C%7Cc%7D)%2C!a%26%26d(%22label%22%2C%7B%22for%22%3Ac%2CinnerHTML%3Ag%7C%7Cc%7D)%2C!a%26%26d(%22input%22%2C%7Btype%3Af%2Cname%3Ac%2Cvalue%3Ae%2Cplaceholder%3Ab%2Crequired%3Ah%2Cstyle%3Ar%7D)%5D)%7Dfunction%20p(a)%7B%22Escape%22%3D%3Da.key%26%26m()%7Dvar%20r%3D%7Bpadding%3A%228px%22%2Ccolor%3A%22var(--fg)%22%2CbackgroundColor%3A%22var(--bg2)%22%2Cwidth%3A%22100%25%22%7D%2Cl%3D%7Bpadding%3A%228px%22%2Ccolor%3A%22var(--fg)%22%2CbackgroundColor%3A%22var(--bg3)%22%7D%3Bl%3Dd(%22form%22%2C%7Baction%3A%22bookmarks%3A%2F%2F%22%2Cmethod%3A%22get%22%2Ctarget%3A%22_blank%22%2Cevents%3A%7Bsubmit%3Am%7D%2Cstyle%3A%7Bpadding%3A%2232px%22%2Ccolor%3A%22var(--fg)%22%2CbackgroundColor%3A%22var(--bg)%22%2CborderRadius%3A%2210px%22%2Cwidth%3A%22400px%22%2Cheight%3A%22auto%22%2Cdisplay%3A%22flex%22%2CflexDirection%3A%22column%22%2CjustifyContent%3A%22space-around%22%2CalignItems%3A%22left%22%2CboxShadow%3A%220%200%2010px%20rgba(0%2C0%2C0%2C0.5)%22%7D%7D%2C%5Bd(%22h2%22%2C%7BinnerHTML%3A%22Add%20Bookmark%22%2Cstyle%3A%7Bcolor%3A%22var(--fg)%22%7D%7D)%2Ck(%7Blabel%3A%22Title%22%2Cname%3A%22title%22%2Cvalue%3Adocument.title%2Crequired%3A!0%7D)%2Ck(%7Blabel%3A%22URI%22%2Cname%3A%22uri%22%2Cvalue%3Adocument.URL%7D)%2Ck(%7Blabel%3A%22Category%22%2Cname%3A%22category%22%2Cvalue%3A%22unsorted%22%2Crequired%3A!0%7D)%2Ck(%7Blabel%3A%22Tags%22%2Cname%3A%22tags%22%2Cvalue%3A%22%22%2Cplaceholder%3A%22Separate%20tags%20with%20commas%22%7D)%2Cd(%22div%22%2C%7Bstyle%3A%7Bdisplay%3A%22flex%22%2CjustifyContent%3A%22space-around%22%2Cpadding%3A%228px%22%2CpaddingTop%3A%2216px%22%2Cwidth%3A%22100%25%22%7D%7D%2C%5Bd(%22input%22%2C%7Btype%3A%22submit%22%2Cvalue%3A%22Save%22%2Cstyle%3Al%7D)%2Cd(%22input%22%2C%7Btype%3A%22button%22%2Cvalue%3A%22Cancel%22%2Cstyle%3Al%2Cevents%3A%7Bclick%3Am%7D%7D)%5D)%5D)%3Bvar%20q%3Dd(%22div%22%2C%7Bstyle%3A%7Bposition%3A%22fixed%22%2Ctop%3A%220%22%2Cleft%3A%220%22%2Cright%3A%220%22%2Cbottom%3A%220%22%2CbackgroundColor%3A%22rgba(0%2C0%2C0%2C0.8)%22%2CzIndex%3A%229999%22%2Cdisplay%3A%22flex%22%2CjustifyContent%3A%22center%22%2CalignItems%3A%22center%22%2C%22--bg%22%3A%22%23eee%22%2C%22--bg2%22%3A%22%23fff%22%2C%22--bg3%22%3A%22%23ddd%22%2C%22--fg%22%3A%22%23111%22%2C%22--fg2%22%3A%22%23333%22%7D%7D%2C%5Bl%5D)%3Bdocument.addEventListener(%22keydown%22%2Cp)%3Bdocument.body.appendChild(q)%7D)()%3Bvoid+0
```

# Firefox Extension

https://github.com/ArtBIT/bash-bookmarks-firefox-add-on/

If you source'd `.bookmarksrc` the server should auto-start, otherwise you need to start it via `bookmarks server`. The server is a HTTP server with a very simple API. 
- Search Endpoint `GET /search?format=json&q=searchterm`
- Add Endpoint `POST /add` which accepts a JSON payload containing `{url,title,category}`

The Firefox Add-On uses these two endpoints to automatically add bash-bookmark whenever a Firefox bookmark is created, and to suggest bookmarks directly from the address-bar by registering `bb` keyword, which when used in the address-bar, fetches the bookmarks results from the server.

