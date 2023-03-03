# CleverAdsSolutions App-ads.txt

[![Updated](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/cleveradssolutions/App-ads.txt/master/Shield.json)](https://github.com/cleveradssolutions/App-ads.txt)

App-ads.txt is a text file app developers upload to their developer website, which lists the ad sources authorized to sell that developer’s inventory. Just like on web, the IAB created a system which allows buyers to know who is authorized to buy and sell specific in-app ad inventory, and who isn’t. This is an important step towards eliminating certain types of fraud, and improving the transparency and efficiency of the overall ecosystem. Most savvy brand marketers and demand side platforms won’t buy inventory that doesn’t have ads.txt implemented. 
A DSP looking to bid on app inventory scans the app-ads.txt file on a developer’s website to verify which ad sources are authorized to sell that app’s inventory. The DSP will only accept bid requests from ad sources listed on the file and authorized by the app developer.  
You can read more about it here: https://iabtechlab.com/ads-txt

> **Warning**  
> If you don't implement app-ads.txt, it may hurt your eCPMs because there will be less advertisers willing to pay you for ads.

We’ve made it easier for you to include CleverAdsSolutions list of entries so that you will never miss any budgets from ironSource’s top brands partners. 
- Combined file including sources from all mediation partners:     
[app-ads.txt](/app-ads.txt)
- File-separated sources for each partner can be found below:  
[Networks](/Networks)  

> **Note**  
> Don’t forget to keep track of the list since it is updated from time to time.  
> Subscribe so you don't miss app-ads.txt updates. [![Subscribe](https://img.shields.io/github/watchers/cleveradssolutions/App-ads.txt?label=Subscribe&style=social)](https://github.com/cleveradssolutions/App-ads.txt/subscription)  

## Updating a Developer Website
It is important to pay attention to the instructions below before beginning the app-ads.txt implementation.
- You must list your **Developer Website URL** in the iTunes and GooglePlay app stores, as relevant.
- There must be a valid developer website URL in all app stores hosting your apps.
- This app-ads.txt guide only addresses Apple's App Store and Google Play stores, with both you can fully comply with the specs of app-ads.txt.
- The Developer Website URL is used by advertising platforms to locate the app-ads.txt file.  

### AppStore
Developer page is listed under **Developer Website**:  
![image](https://user-images.githubusercontent.com/22005013/114005460-3b122e00-9868-11eb-92bb-e8dce76b1b12.png)  

Follow these instructions to either update or add a developer website to the App Store page:
1. On the Apple Developer Program page, click App Store Connect.
2. Select the app for which you want to add a new version.
3. Inside the app, click **+** for **Version or Platform**
4. In the new version add the **Marketing URL**
5. Post the `/app-ads.txt` file on the root folder of your developer website, listing all authorized sellers of their app inventory.  

### GooglePlay
The developer page is listed under **Visit Website**:  
![image](https://user-images.githubusercontent.com/22005013/114006234-f1761300-9868-11eb-952f-176b1937308a.png)  

Follow these instructions to either update or add a developer website to Google Play:
1. On the **Google Play Console** select the game for which you want to add a website
2. On the left menu bar click **Store Presence >> Store Listing**
3. Enter the details of your app
4. Enter your contact details including the **Website**.
5. Post the `/app-ads.txt` file on the root folder of your developer website, listing all authorized sellers of their app inventory.

> **Note**  
> Contact your internal webmaster to post the .txt file on your developer website including all direct and indirect authorized sellers of your inventory.

## Ensure your app-ads.txt files can be crawled
To ensure your app-ads.txt file can be crawled, we recommend working through the following troubleshooting steps.  

> **Note**  
> The following information was taken from a [Google Support resource](https://support.google.com/admob/answer/9679128).

### Confirm that the file is reachable from the root domain
Redirects from `domain.com/app-ads.txt` to `www.domain.com/app-ads.txt` are fairly common. App-ads.txt crawling will start at the root domain. The root domain needs to return from, or redirect to, the app-ads.txt file.  

> **Warning**  
> An app-ads.txt file on `www.domain.com/app-ads.txt` will only be crawled if `domain.com/app-ads.txt` redirects to it.

### Confirm the file is not temporarily unavailable
If a previously seen app-ads.txt file is unavailable on a subsequent re-crawl, the previously seen entries will be:
- Purged if the response is a hard 404 error (page that actually doesn’t exist; HTTP 404 status).
- Retained for up to five days if the response is a soft 404 error (a real page returned for a URL that doesn't actually exist; HTTP 200 status) or a 500 server error.

### Ensure file is returned with an HTTP 200 OK status code
While a request for an app-ads.txt file may return the contents of the file in the response body, if the status code in the response header indicates the file was not found (e.g., status code 404):
- The response will be ignored.
- The file will be considered non-existent.  

Make sure the file has an HTTP 200 OK status code.

### Ensure there are no formatting errors or invalid characters in the file
Formatting errors, such as invalid whitespace characters, may be difficult to detect but can make an app-ads.txt file difficult to parse by a crawler, and may therefore result in a file being ignored. Avoid copying and pasting app-ads.txt entries from a rich text editor; we recommend a plain text editor. You can also check for invalid UTF-8 characters in your app-ads.txt file using a HEX editor. 
