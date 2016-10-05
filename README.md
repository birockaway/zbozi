# Description #

Scraper based extractor component for extraction of cost and transaction data from Zbozi.cz.

## Config ##

The settings is provided through parameters attribute. Here you can set date range through **Date_preset** of **Date_from** and **Date_to** attributes. Furthermore you can set the **Mode** parameter which allows you to geather summary or by_category.



The shop credentials are configured through parameters in configuration. You need to specify login credentials, **Shop_name** and shortcut (which will distinguish output mapping tables) and **Shop_id** which is Zbozi.cz internal ID of a shop nad you will find it in each shop's statistics url in Zbozi's administration UI.



# Parameters options #

* **DATE & MODE PARAMETERS**

	* **Date_preset**:
		* "Yesterday" -> extracts data for yesterday only
		* "last_week" -> extracts data for last 7 days
		* "last_31_days" -> extracts data for last 31 days
		* "last_year" -> extracts data for last year

	**Note**: setting one of foregoing values causes ignoring of **Date_from** and **Date_to** parameters. If invalid **Date_preset** parameter is give, the **Date_from** and **Date_to** parameters are taken into account.

	* **Mode**:
		* "summary" -> extracts data agregated by - shop **x** day **x** metrics. 
		* "by_category" -> extracts data agregated by - shop **x** day **x** product_category **x** metrics.  **!! not yet fully developed !!** - follow code on github to see details. 

* **SHOP CREDENTIALS**	
	
	* **Accounts**:
		* "Account_i" -> distinguishes each account, can be arbitrary string.
	* **Login**:
		* "email@zbozi.cz" -> your login email address to Zbozi.cz service	
	* **Password**:
		* "secret" -> your password to Zbozi.cz service
	* **Shop_name**:
		* ["My_shop_1", "My_shop_2",...,"My_shop_n"] -> list of your shop names on that Zbozi.cz account
	* **Shop_id**:
		* ["1111", "1112",...,"111n"] -> list of your Zbozi.cz shop ID's; see text bellow for details
	* **Shop_shortcut**:
		* ["sh1", "sh2",...,"shn"] -> list of shortcuts for your shop. Can be list of arbitrary strings, that are appended to the *out_zbozi_* csv file in output mapping.

# Zbozi.cz shop ID #
Each shop has it's own shop ID called *premiseId* in the Zbozi.cz environment. You can optain it in Zbozi.cz administration service in each shop detail page ULR. For example if you go to admin.zbozi.cz -> statistiky provozovny and in your URL you should see 
```
https://admin.zbozi.cz/premiseStatisticsOverviewScreen?premiseId=<Shop_id>
```

# Example #

Example configuration of parameters:

```
"parameters": {
        "Date_from": "2016-03-27",
        "Date_to": "2016-04-02",
        "Mode": "summary",
        "Accounts": {
    	"Login_1": {
     		"Login": "foo@eshopy.cz",
     		"Password": "secret",
     		"Shop_name": [
        	"shop_1.cz",
        	"shop_2.cz"
      ],
      "Shop_id": [
        "1234",
        "1235",
      ],
      "Shop_shortcut": [
        "s1",
        "s1"
      ]
    },
    "Login_2": {
      "Login": "bar@othereshop.cz",
      "Password": "so_secret",
      "Shop_name": [
        "other_shop.cz"
      ],
      "Shop_id": [
        "666"
      ],
      "Shop_shortcut": [
        "os"
      ]
    }
    }
```

## Comunication with KBC ##

The extractor is comuticating with KBC through output mapping settings, which configured by standard way (through UI just like it is in any transformation).

**Note**: The json parameters are set up by the Json Schema. See https://developers.keboola.com/extend/registration/configuration-schema/ for more details.
