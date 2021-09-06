#!/bin/sh
cd "$(dirname "$0")"
rm -f app-ads.txt
cat AdMob.txt \
    FBAudienceNetwork.txt \
    AdColony.txt \
    MoPup.txt \
    Pangle.txt \
    IronSource.txt \
    AppLovin.txt \
    FyberFairBid.txt \
    UnityAds.txt \
    Vungle.txt \
    SuperAwesome.txt \
    Kidoz.txt \
    InMobi.txt \
    MyTarget.txt \
    StartIo.txt \
    Chartboost.txt \
    Mintegral.txt \
    Others.txt > app-ads.txt
curr_date=$(date +'%b %d, %Y')
echo "Update ${curr_date}"
sed -i '' -e "1i\\
#Last update ${curr_date}" app-ads.txt
mv -f app-ads.txt ../