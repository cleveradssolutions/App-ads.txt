# CAS.AI Authorized Sellers for Apps (App-ads.txt)

[![Updated](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/cleveradssolutions/App-ads.txt/master/Shield.json)](https://github.com/cleveradssolutions/App-ads.txt)


[app-ads.txt](https://iabtechlab.com/wp-content/uploads/2019/03/app-ads.txt-v1.0-final-.pdf) is a vital text file that app developers upload to their websites, listing the ad sources authorized to sell their inventory. Similar to the web, the IAB has established a system that enables buyers to verify who is permitted to buy and sell specific in-app ad inventory. This initiative plays a crucial role in combating fraud and enhancing transparency and efficiency across the ecosystem. Consequently, most savvy brand marketers and demand-side platforms (DSPs) tend to avoid purchasing inventory without app-ads.txt implementation.

## How app-ads.txt Works for Mobile Apps

When a DSP seeks to bid on app inventory, it scans the app-ads.txt file on the developer’s website to confirm which ad sources are authorized to sell that app’s inventory. The DSP will only accept bid requests from the ad sources listed in this file, ensuring compliance with the developer's authorization.

## Benefits of Implementing app-ads.txt for Your Mobile App

1. **Attract Brand Budgets**  
   Major brands and agencies are more inclined to purchase app inventory through DSPs that verify authorized ad sources. By implementing app-ads.txt, developers signal to DSPs that their inventory is secure. Those who neglect to adopt app-ads.txt risk exclusion from DSPs' targeted media pools.

2. **Combat Ad Fraud**  
   Malicious actors may create counterfeit apps that impersonate legitimate ones, misleading DSPs into spending brand budgets on fraudulent inventory. This not only harms legitimate developers but also deprives them of revenue intended for their apps. Implementing app-ads.txt helps prevent unauthorized impersonation and minimizes instances of fraud, ultimately safeguarding developers’ financial interests.

> **Warning**  
> Failing to implement app-ads.txt could negatively impact your eCPMs, as fewer advertisers may be willing to engage with your app.  
> If you manage multiple domains, ensure that all relevant domains are updated accordingly.

We’ve simplified the process for you to include the CAS.AI list of entries, ensuring you never miss out on budgets from top brand partners:  
- **Combined file** containing sources from all mediation partners:  
  [app-ads.txt](/app-ads.txt)  
- **File-separated sources** for each partner can be found below:  
  [Networks](/Networks)  

You can conveniently use our domain [https://cas.ai](https://cas.ai) as the **Developer Website** for your app, and rest assured that [https://cas.ai/app-ads.txt](https://cas.ai/app-ads.txt) will always be kept up to date.

> **Note**  
> Don’t forget to monitor updates to the file to ensure your app's revenue remains stable.  
> Subscribe to receive notifications about app-ads.txt updates: [![Subscribe](https://img.shields.io/github/watchers/cleveradssolutions/App-ads.txt?label=Subscribe&style=social)](https://github.com/cleveradssolutions/App-ads.txt/subscription)

## Updating a Developer Website
It is important to pay attention to the instructions below before beginning the app-ads.txt implementation.
- You must list your **Developer Website URL** in the iTunes and GooglePlay app stores, as relevant.
- There must be a valid developer website URL in all app stores hosting your apps.
- This app-ads.txt guide only addresses Apple's App Store and Google Play stores, with both you can fully comply with the specs of app-ads.txt.
- The Developer Website URL is used by advertising platforms to locate the app-ads.txt file.  

### AppStore
<details>

Developer page is listed under **Developer Website**:  
![image](https://user-images.githubusercontent.com/22005013/114005460-3b122e00-9868-11eb-92bb-e8dce76b1b12.png)  

Follow these instructions to either update or add a developer website to the App Store page:
1. On the Apple Developer Program page, click App Store Connect.
2. Select the app for which you want to add a new version.
3. Inside the app, click **+** for **Version or Platform**
4. In the new version add the **Marketing URL**
5. Post the `/app-ads.txt` file on the root folder of your developer website, listing all authorized sellers of their app inventory.  
</details>

### GooglePlay
<details>

The developer page is listed under **Visit Website**:  
![image](https://user-images.githubusercontent.com/22005013/114006234-f1761300-9868-11eb-952f-176b1937308a.png)  

Follow these instructions to either update or add a developer website to Google Play:
1. On the **Google Play Console** select the game for which you want to add a website
2. On the left menu bar click **Store Presence >> Store Listing**
3. Enter the details of your app
4. Enter your contact details including the **Website**.
5. Post the `/app-ads.txt` file on the root folder of your developer website, listing all authorized sellers of their app inventory.

</details>

> [!Note]
> Contact your internal webmaster to post the .txt file on your developer website including all direct and indirect authorized sellers of your inventory.

## Ensure your app-ads.txt files can be crawled
To ensure your app-ads.txt file can be crawled, we recommend working through the following troubleshooting steps.  

> [!Note] 
> The following information was taken from a [Google Support resource](https://support.google.com/admob/answer/9679128).

### Confirm that the file is reachable from the root domain
Redirects from `domain.com/app-ads.txt` to `www.domain.com/app-ads.txt` are fairly common. App-ads.txt crawling will start at the root domain. The root domain needs to return from, or redirect to, the app-ads.txt file.  

> [!Warning]
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

## Support
Seek assistance via `support@cas.ai`
