#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import json
import re
import shutil
import subprocess
import textwrap
import unicodedata
from html import escape
from pathlib import Path
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
DATA = ROOT / "data"
MEDIA = ROOT / "media"
DIST = ROOT / "dist"
ASSETS = DIST / "assets"
OG = DIST / "og"
CACHE = ROOT / ".cache"
FONT_DIR = CACHE / "fonts"
QR_DIR = CACHE / "qr"

PLACEHOLDER_NAME = "placeholder.png"
FONT_REGULAR = FONT_DIR / "NotoSansCJKsc-Regular.otf"
FONT_BOLD = FONT_DIR / "NotoSansCJKsc-Bold.otf"
FONT_URLS = {
    FONT_REGULAR: "https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf",
    FONT_BOLD: "https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Bold.otf",
}

CATEGORY_ZH = {
    "Computer Supplies": "电脑用品",
    "Electronics": "电子产品",
    "Furniture": "家具",
    "Household": "家居用品",
}

CONDITION_ZH = {
    "New - sealed": "全新未拆封",
    "Used - good": "二手 - 状况良好",
}

ITEM_ZH = {
    "cat6-cable-2pack-10ft": {
        "name": "Inland CAT6 网线双包装 10 英尺",
        "description": "两根 10 英尺 CAT6 RJ45 网线（黑色和蓝色），裸铜线芯，原包装未拆封。",
        "pickupNotes": "小件，适合和其他电脑用品一起打包带走。",
    },
    "sony-srs-xb23": {
        "name": "Sony EXTRA BASS SRS-XB23 蓝牙音箱",
        "description": "便携式 Sony EXTRA BASS 蓝牙音箱，型号 SRS-XB23，带原包装盒。",
        "pickupNotes": "包含照片中展示的原装零售包装盒。",
    },
    "rog-swift-pg329q-monitor": {
        "name": "ASUS ROG Swift PG329Q 显示器",
        "description": "ASUS ROG Swift PG329Q 游戏显示器，包含原包装箱。",
        "pickupNotes": "包含原包装箱，可按需提供更多照片。",
    },
    "bose-companion-2-series-iii": {
        "name": "Bose Companion 2 Series III 音箱",
        "description": "Bose Companion 2 Series III 多媒体音箱，带电源适配器和连接线。",
        "pickupNotes": "包含三张照片：正面、背部接口和型号标签。",
    },
    "lamicall-laptop-stand": {
        "name": "Lamicall 笔记本电脑支架",
        "description": "可调节铝合金 Lamicall 笔记本支架，照片中带原包装盒。",
        "pickupNotes": "可折叠可调节支架，照片中含原包装盒。",
    },
    "ikea-elloven-monitor-stand-drawer": {
        "name": "IKEA ELLOVEN 带抽屉显示器增高架",
        "description": "IKEA ELLOVEN 显示器增高架，竹制抽屉，白色台面，照片中可见展开状态与标签。",
        "pickupNotes": "包含两张照片：抽屉展开视图和产品标签/参考贴纸。",
    },
    "asus-vp28uqg-monitor-arm": {
        "name": "ASUS VP28UQG 28 英寸 4K 显示器（带桌夹支架）",
        "description": "ASUS VP28UQG 28 英寸 4K 显示器，已安装可调节桌夹支架，附带 DP 线。",
        "pickupNotes": "已安装可调节桌夹支架。包含三张照片：正面、背部和型号标签。",
    },
    "flexispot-e7-standing-desk-govee": {
        "name": "FlexiSpot Pro 升降桌（E7）+ Govee RGBIC 桌面灯带",
        "description": "FlexiSpot Pro 升降桌（E7）套餐，包含照片中展示的 Govee RGBIC 桌面灯带。",
        "pickupNotes": "套餐包含 FlexiSpot E7 升降桌和桌面上的 Govee RGBIC 灯带。四张照片：已组装桌架、零件视图、整桌视图和配件近景。",
    },
    "big-joe-comfort-chair": {
        "name": "Big Joe 舒适懒人椅",
        "description": "Big Joe 风格黑色舒适豆袋/懒人椅。",
        "pickupNotes": "柔软的大号懒人豆袋椅。",
    },
    "hp-envy-6155e-printer-bundle": {
        "name": "HP Envy 6155e 打印机套装",
        "description": "HP Envy 6155e 一体机套装，包含额外黑色墨盒和照片中展示的 HP Premium 24 打印纸。",
        "pickupNotes": "套装包含额外黑色墨盒和 HP Premium 24 打印纸。",
    },
    "honeywell-quietset-8-fan": {
        "name": "Honeywell QuietSet 8 40英寸塔扇",
        "description": "Honeywell QuietSet 8 全房间 40 英寸塔扇，照片中带原包装箱。",
        "pickupNotes": "包含两张照片：带包装箱的整机图和顶部控制面板近景。",
    },
    "herman-miller-aeron-chair-size-b": {
        "name": "Herman Miller Aeron 人体工学椅（全功能，B号）",
        "description": "Herman Miller Aeron 人体工学椅，全功能配置，B 号尺寸。包含正面和侧面两张照片。",
        "pickupNotes": "全功能 B 号 Aeron，包含两张照片。",
    },
    "whiteboard-bundle-two-boards-markers": {
        "name": "两块白板 + 三色白板笔套装",
        "description": "套装包含两块可擦写白板，以及一组三色 Pilot V Board Master 白板笔。",
        "pickupNotes": "套装包含两块白板和一组 Pilot 白板笔。",
    },
    "floor-lamp-generic": {
        "name": "落地灯",
        "description": "黑色落地灯，带两个白色灯罩，照片中为已组装并可正常使用状态。",
        "pickupNotes": "标准双灯头落地灯。",
    },
    "ikea-skadis-pegboard-set": {
        "name": "IKEA SKÅDIS 洞洞板套装",
        "description": "IKEA SKÅDIS 白色洞洞板套装，包含挂篮、小盒、托盘、挂钩和夹具等配件，照片中展示为整套。",
        "pickupNotes": "套装包含照片中的挂篮、挂钩、托盘等配件。",
    },
    "flexispot-slim-desk-drawer-s07lb": {
        "name": "FlexiSpot 超薄桌下收纳抽屉 S07LB",
        "description": "FlexiSpot 超薄桌下收纳抽屉，型号 S07LB，照片中展示原包装箱。",
        "pickupNotes": "超薄桌下收纳抽屉，照片中含原包装盒。",
    },
    "frigidaire-gallery-mini-fridge": {
        "name": "Frigidaire Gallery 迷你美妆冰箱（6罐装）",
        "description": "Frigidaire Gallery 迷你美妆冰箱 / 小型冷藏箱，照片中展示了原包装盒和电源配件。",
        "pickupNotes": "小型台面迷你冰箱，照片中含原包装箱和配件。",
    },
    "frigidaire-countertop-ice-maker": {
        "name": "Frigidaire 台面制冰机（每日 26 磅）",
        "description": "Frigidaire 台面制冰机，标称每日制冰 26 磅，照片中展示了原包装箱。",
        "pickupNotes": "台面制冰机，照片中含原包装箱。",
    },
    "goveelife-air-purifier-h7120": {
        "name": "GoveeLife 空气净化器 H7120",
        "description": "GoveeLife 空气净化器，型号 H7120，照片中展示了原包装箱。",
        "pickupNotes": "空气净化器，照片中含原包装箱。",
    },
    "ikea-kallax-shelf-drawers": {
        "name": "IKEA KALLAX 书架 + 折叠抽屉套装",
        "description": "黑棕色 IKEA KALLAX 风格格架，包含折叠布抽屉套装。",
        "pickupNotes": "照片中展示了已组装的架子，顶部放着折叠抽屉，另有一个抽屉已装入格架。",
    },
    "shelf-floor-lamp-black": {
        "name": "黑色置物落地灯",
        "description": "黑色置物落地灯，自带多层置物架和白色布艺灯罩。",
        "pickupNotes": "包含两张照片：整体组装视图和顶部灯罩视图。",
    },
    "black-tv-stand": {
        "name": "黑色电视桌",
        "description": "简洁的黑色电视桌 / 媒体桌，下方带一层置物板。",
        "pickupNotes": "紧凑型电视 / 媒体桌。",
    },
    "table-lamp-white-fabric-shade": {
        "name": "白色布罩台灯",
        "description": "小型白色台灯，配布艺灯罩，照片中分别展示了亮灯和未亮灯状态。",
        "pickupNotes": "包含两张照片：关闭状态和点亮状态。",
    },
    "queen-bed-frame-klv-up-088": {
        "name": "KLV-UP-088 易组装大号床架",
        "description": "易于组装的大号床架，黑色软包菱格床头，型号 KLV-UP-088。",
        "pickupNotes": "包含两张照片：正面视图和斜角视图。不含床垫。",
    },
    "lego-minecraft-creeper-21276": {
        "name": "乐高 Minecraft 苦力怕 21276（含玻璃展示罩）",
        "description": "乐高 Minecraft 21276 苦力怕套装，照片中为已拼装状态，并放在玻璃展示罩中安全展示。",
        "pickupNotes": "照片中包含原盒，以及放在玻璃罩里的已拼装苦力怕。",
    },
    "crate-barrel-tate-nightstand": {
        "name": "Crate & Barrel Tate 床头柜",
        "description": "Crate & Barrel Tate 床头柜，暖木色，一只抽屉加一层开放置物格。",
        "pickupNotes": "包含两张照片：正面视图和抽屉打开视图。",
    },
    "small-rolling-cart-black": {
        "name": "黑色迷你移动小推车",
        "description": "黑色迷你滚轮收纳/移动小推车，占地小，可自定义层板配置。",
        "pickupNotes": "照片中展示了已组装小推车、松开的层板以及附带五金件。",
    },
    "hanging-closet-organizer-6-shelf": {
        "name": "悬挂式衣柜收纳层架",
        "description": "布艺悬挂式衣柜收纳层架，带多个隔层，照片中展示了展开和折叠状态。",
        "pickupNotes": "包含两张照片：展开悬挂视图和折叠状态。",
    },
    "over-door-basket-organizer-white": {
        "name": "白色门后双层收纳篮",
        "description": "白色门后双层收纳篮，带木纹层板。",
        "pickupNotes": "白色门后双层收纳篮，带木纹层板。",
    },
    "over-door-hook-rack-white": {
        "name": "白色门后挂钩架",
        "description": "白色门后挂钩架，下方有五个挂钩。",
        "pickupNotes": "白色门后挂钩架，下方有五个挂钩。",
    },
    "over-door-hook-rack-black": {
        "name": "黑色门后挂钩架",
        "description": "黑色门后挂钩架，下方有五个挂钩。",
        "pickupNotes": "黑色门后挂钩架，下方有五个挂钩。",
    },
    "dyson-hair-dryer-with-case": {
        "name": "戴森吹风机（含收纳盒）",
        "description": "戴森吹风机，附带照片中的紫色收纳/展示盒。仅凭当前图片无法确认具体型号。",
        "pickupNotes": "包含照片中的紫色收纳盒。",
    },
    "goveelife-smart-humidifier": {
        "name": "GoveeLife 智能加湿器",
        "description": "白色 GoveeLife 智能加湿器，附带电源适配器。仅凭当前照片无法确认具体型号。",
        "pickupNotes": "白色智能加湿器，适合卧室或桌面使用。",
    },
    "pen-gear-stapler-set": {
        "name": "Pen+Gear 订书机套装",
        "description": "Pen+Gear 订书机套装，包含黑色订书机、起钉器和多盒标准订书钉。",
        "pickupNotes": "照片中展示的是整套一起出售：订书机、起钉器和订书钉。",
    },
    "utility-knife-set-black": {
        "name": "黑色美工刀套装",
        "description": "黑色多件装美工刀 / 裁纸刀套装，盒内含多把独立包装的小刀。",
        "pickupNotes": "照片中展示的是整套一起出售，不是单把刀。",
    },
    "yellow-mailing-envelopes-40plus": {
        "name": "邮寄信封（剩余 40+ 个）",
        "description": "黄色邮寄信封一包，原包装为 50 个装，目前剩余超过 40 个。",
        "pickupNotes": "原包装标签显示 50 count；当前剩余数量为 40 多个信封。",
    },
    "cuisinart-electric-coffee-grinder-black": {
        "name": "Cuisinart 电动咖啡豆研磨机",
        "description": "黑色 Cuisinart 电动咖啡豆研磨机，带电源线。仅凭当前照片无法确认具体型号。",
        "pickupNotes": "小型电动研磨机，带透明豆仓。",
    },
    "amazon-basics-coffee-filters-basket": {
        "name": "Amazon Basics 篮式咖啡滤纸",
        "description": "已开封的 Amazon Basics 篮式咖啡滤纸，包装标签显示为 200 张。",
        "pickupNotes": "这是已开封包装，不是全新未拆封。",
    },
    "mesh-file-organizers-2pack-white": {
        "name": "白色网格文件收纳架两件套",
        "description": "两只白色金属网格文件收纳架 / 杂志架，一起作为两件套出售。",
        "pickupNotes": "照片中两只收纳架一起出售，此条目对应整套。",
    },
    "chemical-safety-goggles-clear": {
        "name": "化学实验护目镜",
        "description": "透明化学实验 / 安全护目镜，带可调节黑色松紧带。",
        "pickupNotes": "可调节护目镜，属于全眼罩式防泼溅设计。",
    },
    "ninja-blender-auto-iq-black": {
        "name": "Ninja Auto-iQ 搅拌机",
        "description": "黑色 Ninja 台式搅拌机，带大容量搅拌杯和 Auto-iQ 控制面板。仅凭当前照片无法确认具体型号。",
        "pickupNotes": "大容量搅拌杯款，带 Auto-iQ 控制面板。",
    },
    "bear-mini-rice-cooker-green": {
        "name": "Bear 迷你电饭煲",
        "description": "小型 Bear 电饭煲，带可拆卸不粘内胆和翻盖。仅凭当前照片无法确认具体型号。",
        "pickupNotes": "小型电饭煲，带可拆卸不粘内胆。",
    },
    "ikea-dining-table-dark-brown": {
        "name": "IKEA 餐桌",
        "description": "深棕色 IKEA 风格长方形餐桌。仅凭当前照片无法确认具体 IKEA 型号。",
        "pickupNotes": "仅包含桌子本体。",
    },
    "black-dining-chair-generic": {
        "name": "黑色餐椅",
        "description": "通用黑色餐椅，靠背为交叉设计。价格按单把计算。",
        "pickupNotes": "按单把计价。交叉靠背餐椅，包含两张照片。",
    },
    "twin-bed-frame-white": {
        "name": "单人床架",
        "description": "白色单人床架，带较高床头板和低矮侧边框。",
        "pickupNotes": "仅包含床架本体，不含床垫、枕头、床单和周围其他家具。",
    },
    "space-heater-black-compact": {
        "name": "黑色暖风机",
        "description": "黑色小型便携暖风机，顶部带提手。",
        "pickupNotes": "此条目仅对应小黑色暖风机本体。",
    },
    "oil-filled-radiator-heater-white": {
        "name": "白色油汀暖气片",
        "description": "白色油汀式暖气片，带滚轮和前部控制旋钮。",
        "pickupNotes": "此条目仅对应白色油汀暖气片本体。",
    },
    "folding-saucer-chair-black": {
        "name": "黑色折叠懒人沙发椅",
        "description": "黑色折叠式圆盘懒人沙发椅，带软垫圆形坐面和金属支架。",
        "pickupNotes": "仅包含椅子本体，不含旁边的台灯、电线和房间内其他物品。",
    },
    "floor-lamp-black-room": {
        "name": "黑色地灯",
        "description": "照片里展示的黑色落地灯。",
        "pickupNotes": "此条目仅包含地灯本体，不含旁边的椅子和房间内其他物品。",
    },
    "nightstand-black-single-drawer": {
        "name": "黑色床头柜",
        "description": "黑色床头柜，带一层开放置物格和一个下方抽屉。",
        "pickupNotes": "此条目仅包含床头柜本体，不含台灯和旁边其他物品。",
    },
    "table-lamp-rectangular-shade-black-base": {
        "name": "长方形灯罩台灯",
        "description": "台灯带长方形白色灯罩和黑色方形底座。",
        "pickupNotes": "此条目仅包含台灯本体，不含床头柜和旁边其他物品。",
    },
}

SITE_I18N = {
    "en": {
        "htmlLang": "en",
        "numberLocale": "en-US",
        "subtitle": "A graduation sale where buyers guess the price before they unlock it.",
        "defaultDescription": "Furniture and computer supplies for sale before graduation. Browse the goods, guess the price to unlock a deal, and schedule pickup or delivery by email.",
        "sharingTagline": "Guess the price. Unlock the deal.",
        "deliveryNote": "Orders above $50 qualify for free local delivery.",
        "pickupNote": "Pickup details are coordinated by email after checkout.",
        "strings": {
            "brandTagline": "Graduation sale · price guessing",
            "homeNav": "Home",
            "aboutNav": "About",
            "cartNav": "Cart",
            "cartCounterLabel": "unlocked item(s)",
            "guessModeLabel": "Guess mode",
            "plainModeLabel": "Plain mode",
            "modeChooserTitle": "Choose how visitors see prices",
            "modeChooserBody": "Plain mode is the default share link. Guess mode is the bonus version.",
            "modeGuessButton": "Open bonus guessing version",
            "modePlainButton": "Open plain version",
            "listedPrice": "Listed price",
            "actualPriceLabel": "Actual price",
            "plainModeNotice": "Plain version — actual price shown directly.",
            "hideSoldOut": "Hide sold out",
            "showingItems": "Showing {shown} of {total}",
            "loadingMore": "Scroll down to load more items",
            "qrCodeLabel": "QR code",
            "searchPlaceholder": "Search furniture, monitors, supplies...",
            "availableItemsTitle": "Available items",
            "availableItemsDesc": "Furniture, computer supplies, and anything else that needs a new home before graduation.",
            "aboutHeroTitle": "Guess the price. Unlock the deal.",
            "aboutHeroBody": "Congo is a graduation-sale storefront for local pickup and delivery. The front page stays focused on browsing goods; this page explains the shopping mechanic.",
            "howItWorksTitle": "How it works",
            "howItWorksItems": [
                "Each product page starts with a hidden seller checkout price.",
                "You can make up to 3 offers per item from the same browser.",
                "If your offer is too low, the site asks you to try again.",
                "If your offer succeeds, the site unlocks a checkout price and lets you add the item to cart.",
                "Unlocked items can be bundled for pickup or local delivery.",
                "Orders above {threshold} qualify for free local delivery.",
                "The final checkout page prepares a ready-to-send email to {email} for scheduling.",
            ],
            "referencePriceLabel": "Reference price",
            "quantityLabel": "Quantity",
            "earliestPickupLabel": "Earliest pickup",
            "latestPickupLabel": "Latest pickup",
            "pickupNoteLabel": "Pickup note",
            "availableNow": "Available now",
            "unlockTitle": "I will decide the checkout price.",
            "unlockSubtitle": "Enter your willing to pay.",
            "guessInputPlaceholder": "Enter your guess price to make a deal.",
            "offersLeft": "Offers left: {count}",
            "hiddenCheckoutPrice": "The checkout price is still hidden.",
            "guessButton": "Guess",
            "addToCart": "Add to cart",
            "checkoutNow": "Checkout now",
            "statusAvailable": "available",
            "statusPending": "pending",
            "statusUnavailable": "Unavailable",
            "statusSold": "Sold out",
            "threeChances": "3 chances",
            "priceHiddenUntilGuess": "Price hidden until you guess high enough",
            "generatedNegotiablePrice": "{price} (negotiable)",
            "unlockedOffer": "Unlocked offer: {price}",
            "noMatchTitle": "No items matched that search.",
            "noMatchDesc": "Try another keyword or another category.",
            "allCategory": "All",
            "pendingItemMessage": "This item is not ready for offers yet.",
            "pendingItemHint": "Seller has not enabled guessing for this item yet.",
            "enterValidAmount": "Enter a valid dollar amount first.",
            "guessSuccess": "Yes — that guess works. The unlocked checkout price is shown below.",
            "unlockAtSellerPrice": "Unlocked at the seller price.",
            "unlockAboveTarget": "Unlocked from an above-target guess.",
            "guessTooLow": "Too low. Try again — {count} chance{suffix} left.",
            "guessTooLowFinal": "Too low, and that was the last chance on this browser.",
            "noGuessesLeft": "No guesses left on this browser.",
            "lastTryMessage": "That was the last try from this browser. If you still want it, email the seller directly.",
            "added": "Added",
            "checkoutTitle": "Checkout",
            "checkoutDesc": "Unlock items first, then use this page to compose the pickup or delivery email.",
            "clearCart": "Clear cart",
            "orderSummary": "Order summary",
            "itemsLabel": "Items",
            "totalLabel": "Total",
            "deliveryNeedMore": "Add {amount} more to reach free local delivery.",
            "deliveryUnlocked": "Free local delivery unlocked on this order.",
            "checkoutAddressedTo": "Checkout email will be addressed to {email}.",
            "yourName": "Your name",
            "yourEmail": "Your email",
            "yourPhone": "Phone / Telegram / Signal",
            "preferredTime": "Preferred time",
            "pickupOption": "Pickup",
            "localDeliveryOption": "Local delivery",
            "eitherWorksOption": "Either works",
            "pickupPoint": "Pickup point or delivery area",
            "notesPlaceholder": "Any schedule details, questions, or bundle offers",
            "copyEmailText": "Copy email text",
            "openEmailDraft": "Open email draft",
            "copied": "Copied",
            "copyFailed": "Copy failed",
            "cartEmptyTitle": "Your cart is empty.",
            "cartEmptyDesc": "Unlock an item first, then add it to cart.",
            "backToCatalog": "Back to the catalog",
            "remove": "Remove",
            "unlockedFromGuess": "Unlocked from guess {guess}.",
            "unlockedPriceReady": "Unlocked price ready.",
            "emailGreeting": "Hi {name},",
            "emailIntro": "I would like to buy these items from Congo:",
            "emailTotal": "Total: {total}",
            "emailDeliveryUnlocked": "This order is above {threshold}, so it qualifies for free local delivery.",
            "emailDeliveryNeedMore": "This order is below {threshold}. Pickup is fine, or we can discuss delivery.",
            "emailPreferredOption": "Preferred option: {value}",
            "emailPreferredTime": "Preferred time: {value}",
            "emailName": "Name: {value}",
            "emailEmail": "Email: {value}",
            "emailPhone": "Phone: {value}",
            "emailAddress": "Address / meeting point: {value}",
            "emailNotes": "Notes:",
            "none": "None",
            "thanks": "Thanks!",
            "mailSubject": "Congo order request ({count} item{suffix})",
            "failedLoadCatalog": "Failed to load the catalog: {message}",
            "footerBuildHint": "",
            "langEnglish": "English",
            "langChinese": "中文",
            "langSwitchLabel": "Language",
            "posterQrCaption": "Scan for details",
            "posterDefaultTitle": "Congo : graduate selling.",
            "posterCategoryLine": "{category} · Guess high enough to unlock the checkout price",
        },
    },
    "zh": {
        "htmlLang": "zh-CN",
        "numberLocale": "zh-CN",
        "subtitle": "一个毕业搬家出售站点：先猜价，再解锁成交价。",
        "defaultDescription": "毕业前出售家具和电脑用品。先浏览商品，猜价解锁成交价，再通过邮件预约自提或本地配送。",
        "sharingTagline": "猜价格，解锁成交。",
        "deliveryNote": "订单满 $50 可享受本地免费配送。",
        "pickupNote": "自提或配送时间会在结账邮件中协调。",
        "strings": {
            "brandTagline": "毕业出售 · 猜价成交",
            "homeNav": "首页",
            "aboutNav": "规则",
            "cartNav": "购物车",
            "cartCounterLabel": "件已解锁",
            "guessModeLabel": "猜价版",
            "plainModeLabel": "直售价版",
            "modeChooserTitle": "选择给访客看的价格模式",
            "modeChooserBody": "直售价版是默认分享链接，猜价版作为额外玩法。",
            "modeGuessButton": "打开加分彩蛋猜价版",
            "modePlainButton": "打开直售价版",
            "listedPrice": "现价",
            "actualPriceLabel": "实际价格",
            "plainModeNotice": "直售价版本——直接显示实际价格。",
            "hideSoldOut": "隐藏已售出",
            "showingItems": "已显示 {shown} / {total}",
            "loadingMore": "向下滚动以加载更多商品",
            "qrCodeLabel": "二维码",
            "searchPlaceholder": "搜索家具、显示器、电脑用品……",
            "availableItemsTitle": "在售商品",
            "availableItemsDesc": "家具、电脑用品，以及毕业前需要转手的其他物件。",
            "aboutHeroTitle": "猜价格，解锁成交。",
            "aboutHeroBody": "Congo 是一个支持本地自提和配送的毕业出售站点。首页专注于浏览商品，这一页解释购买规则。",
            "howItWorksTitle": "购买方式",
            "howItWorksItems": [
                "每个商品页面都有一个隐藏的卖家成交价。",
                "同一浏览器下，每件商品最多可以出价 3 次。",
                "如果出价太低，网站会提示你再试一次。",
                "如果出价成功，网站会解锁成交价，并允许加入购物车。",
                "解锁后的商品可以一起打包，自提或本地配送。",
                "订单满 {threshold} 可享受本地免费配送。",
                "中文结账页会显示微信二维码，扫码后联系卖家安排时间。",
            ],
            "referencePriceLabel": "参考价格",
            "quantityLabel": "数量",
            "earliestPickupLabel": "最早可取",
            "latestPickupLabel": "最晚可取",
            "pickupNoteLabel": "取货说明",
            "availableNow": "随时可取",
            "unlockTitle": "我要砍价",
            "unlockSubtitle": "输入自选价格，",
            "guessInputPlaceholder": "输入自选价格，",
            "offersLeft": "剩余出价次数：{count}",
            "hiddenCheckoutPrice": "成交价仍然隐藏。",
            "guessButton": "出价",
            "addToCart": "加入购物车",
            "checkoutNow": "立即结账",
            "statusAvailable": "在售",
            "statusPending": "待定价格",
            "statusUnavailable": "暂不可售",
            "statusSold": "已售出",
            "threeChances": "3 次机会",
            "priceHiddenUntilGuess": "价格会在你猜得足够高时解锁",
            "generatedNegotiablePrice": "{price}（可砍价）",
            "unlockedOffer": "已解锁成交价：{price}",
            "noMatchTitle": "没有匹配该搜索的商品。",
            "noMatchDesc": "试试其他关键词或分类。",
            "allCategory": "全部",
            "pendingItemMessage": "这件商品暂时还不能出价。",
            "pendingItemHint": "卖家还没有为这件商品开放猜价。",
            "enterValidAmount": "请先输入有效金额。",
            "guessSuccess": "砍价成功。",
            "unlockAtSellerPrice": "已按卖家成交价解锁。",
            "unlockAboveTarget": "超过目标价后已解锁成交价。",
            "guessTooLow": "不卖，卖家宁愿直接扔了。",
            "guessTooLowFinal": "不卖，卖家宁愿直接扔了。",
            "noGuessesLeft": "这个浏览器已经没有出价机会了。",
            "lastTryMessage": "这是这个浏览器的最后一次尝试。如果你仍然想要它，可以直接发邮件联系卖家。",
            "added": "已加入",
            "checkoutTitle": "结账",
            "checkoutDesc": "先解锁商品，再在这里查看总价并扫码微信联系。",
            "clearCart": "清空购物车",
            "orderSummary": "订单摘要",
            "itemsLabel": "件数",
            "totalLabel": "总价",
            "deliveryNeedMore": "再加 {amount} 即可享受本地免费配送。",
            "deliveryUnlocked": "该订单已解锁本地免费配送。",
            "checkoutAddressedTo": "结账邮件将发送给 {email}。",
            "yourName": "你的名字",
            "yourEmail": "你的邮箱",
            "yourPhone": "电话 / Telegram / Signal",
            "preferredTime": "希望的时间",
            "pickupOption": "自提",
            "localDeliveryOption": "本地配送",
            "eitherWorksOption": "都可以",
            "pickupPoint": "自提地点或配送区域",
            "notesPlaceholder": "任何时间安排、问题或打包购买想法",
            "copyEmailText": "复制邮件内容",
            "openEmailDraft": "打开邮件草稿",
            "copied": "已复制",
            "copyFailed": "复制失败",
            "cartEmptyTitle": "购物车还是空的。",
            "cartEmptyDesc": "先解锁商品，然后再加入购物车。",
            "backToCatalog": "返回商品页",
            "remove": "移除",
            "unlockedFromGuess": "由出价 {guess} 解锁。",
            "unlockedPriceReady": "成交价已准备好。",
            "emailGreeting": "你好 {name}，",
            "emailIntro": "我想购买 Congo 上的这些商品：",
            "emailTotal": "总价：{total}",
            "emailDeliveryUnlocked": "该订单高于 {threshold}，因此符合本地免费配送条件。",
            "emailDeliveryNeedMore": "该订单低于 {threshold}。可以自提，或者我们也可以再讨论配送。",
            "emailPreferredOption": "偏好的方式：{value}",
            "emailPreferredTime": "偏好的时间：{value}",
            "emailName": "姓名：{value}",
            "emailEmail": "邮箱：{value}",
            "emailPhone": "电话：{value}",
            "emailAddress": "地址 / 碰面地点：{value}",
            "emailNotes": "备注：",
            "none": "无",
            "thanks": "谢谢！",
            "mailSubject": "Congo 订单请求（{count} 件商品）",
            "failedLoadCatalog": "加载商品目录失败：{message}",
            "footerBuildHint": "",
            "langEnglish": "English",
            "langChinese": "中文",
            "langSwitchLabel": "语言",
            "posterQrCaption": "扫码查看详情",
            "posterDefaultTitle": "Congo：毕业出售",
            "posterCategoryLine": "{category} · 猜到足够高即可解锁成交价",
        },
    },
}


def read_catalog() -> dict:
    with (DATA / "catalog.json").open("r", encoding="utf-8") as fh:
        catalog = json.load(fh)
    if "site" not in catalog or "items" not in catalog:
        raise SystemExit("catalog.json must contain 'site' and 'items'.")
    seen = set()
    for item in catalog["items"]:
        item_id = item.get("id")
        if not item_id:
            raise SystemExit("Every item needs a non-empty 'id'.")
        if item_id in seen:
            raise SystemExit(f"Duplicate item id: {item_id}")
        seen.add(item_id)
    return catalog


def ensure_clean_dist() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)
    for path in [OG, ASSETS, DIST / "data", DIST / "item", DIST / "checkout", DIST / "about", DIST / "en", DIST / "zh"]:
        path.mkdir(parents=True, exist_ok=True)


def copy_static_assets() -> None:
    shutil.copy2(SRC / "styles.css", ASSETS / "styles.css")
    shutil.copy2(SRC / "app.js", ASSETS / "app.js")
    if MEDIA.exists():
        shutil.copytree(MEDIA, DIST / "media", dirs_exist_ok=True)
    (DIST / ".nojekyll").write_text("", encoding="utf-8")


def slug(item_id: str) -> str:
    return item_id


def wrap_lines(text: str, width: int, max_lines: int = 3) -> list[str]:
    lines = textwrap.wrap(str(text), width=width) or [str(text)]
    if len(lines) > max_lines:
        lines = lines[: max_lines - 1] + [lines[max_lines - 1][: max(0, width - 1)] + "…"]
    return lines


def money(value: float | int | str, site: dict) -> str:
    currency = site.get("currency", "USD")
    number = float(value or 0)
    if currency == "USD":
        return f"${number:,.2f}".replace(".00", "")
    return f"{currency} {number:,.2f}".replace(".00", "")


def run_convert(args: list[str]) -> None:
    subprocess.run(["convert", *args], check=True)


def fetch_bytes(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=60) as r:
        return r.read()


def ensure_fonts() -> None:
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    for path, url in FONT_URLS.items():
        if not path.exists():
            path.write_bytes(fetch_bytes(url))


def ensure_qr_png(target_url: str) -> Path:
    QR_DIR.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha1(target_url.encode("utf-8")).hexdigest()[:16]
    path = QR_DIR / f"{digest}.png"
    if path.exists():
        return path
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&margin=0&data={quote_plus(target_url)}"
    try:
        path.write_bytes(fetch_bytes(qr_url))
    except Exception:
        run_convert([
            "-size", "180x180", "xc:white",
            "-fill", "black",
            "-draw", "rectangle 10,10 170,170",
            "-fill", "white",
            "-draw", "rectangle 24,24 156,156",
            str(path),
        ])
    return path


def ensure_square_card_image(image_path: str | None, size: int = 420) -> Path:
    out_dir = CACHE / "og-images"
    out_dir.mkdir(parents=True, exist_ok=True)
    source = ROOT / str(image_path or "")
    if not source.exists():
        source = ASSETS / PLACEHOLDER_NAME
    digest = hashlib.sha1(f"{source}:{size}".encode("utf-8")).hexdigest()[:16]
    out = out_dir / f"{digest}.png"
    if out.exists():
        return out
    run_convert([
        str(source),
        "-auto-orient",
        "-resize", f"{size}x{size}^",
        "-gravity", "center",
        "-extent", f"{size}x{size}",
        str(out),
    ])
    return out


def rel_prefix(from_dir: Path, to_dir: Path) -> str:
    rel = Path(shutil.os.path.relpath(to_dir, from_dir))
    s = rel.as_posix()
    return "./" if s == "." else s.rstrip("/") + "/"


def rel_asset(path: str, asset_root: str) -> str:
    return asset_root + path.lstrip("/")


def create_placeholder_png(path: Path) -> None:
    run_convert([
        "-size", "900x900", "gradient:#f7f8fa-#e4ebf1",
        "-fill", "#c7d2db",
        "-draw", "roundrectangle 80,80 820,820 46,46",
        "-fill", "#6b7c8c",
        "-font", str(FONT_BOLD),
        "-gravity", "center",
        "-pointsize", "54",
        "-annotate", "+0-16", "Add a product photo",
        "-font", str(FONT_REGULAR),
        "-pointsize", "28",
        "-annotate", "+0+44", "Place image files in /media and rebuild",
        str(path),
    ])


def create_favicon(path: Path) -> None:
    path.write_text(
        """<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 120 120\">\n  <defs>\n    <linearGradient id=\"g\" x1=\"0%\" y1=\"0%\" x2=\"100%\" y2=\"100%\">\n      <stop offset=\"0%\" stop-color=\"#0f7c5a\"/>\n      <stop offset=\"100%\" stop-color=\"#1ea672\"/>\n    </linearGradient>\n  </defs>\n  <rect width=\"120\" height=\"120\" rx=\"28\" fill=\"url(#g)\"/>\n  <path d=\"M34 78V42h17c21 0 35 7 35 18 0 7-5 13-14 16l18 22H71L56 79h-6v19H34zm16-12h6c8 0 14-2 14-8 0-5-6-7-14-7h-6v15z\" fill=\"white\"/>\n</svg>\n""",
        encoding="utf-8",
    )


def create_poster_png(path: Path, *, site: dict, lang: str, title: str, subtitle_lines: list[str], footer: str, qr_target: str, item: dict | None = None) -> None:
    qr_path = ensure_qr_png(qr_target)
    tmp = path.with_suffix(".tmp.png")
    top_title = site["strings"].get("posterDefaultTitle", site.get("title", "Congo"))

    if item is None:
        caption = site["strings"]["posterQrCaption"]
        run_convert([
            "-size", "1200x630", "gradient:#131a22-#243b55",
            "-fill", "#f3a847", "-draw", "rectangle 0,0 1200,96",
            "-fill", "#131a22", "-font", str(FONT_BOLD), "-gravity", "northwest",
            "-pointsize", "42", "-annotate", "+56+26", top_title,
            "-fill", "white", "-font", str(FONT_BOLD), "-pointsize", "68",
            "-annotate", "+56+150", wrap_lines(title, 20, max_lines=1)[0],
            *(sum(([
                "-fill", "white",
                "-font", str(FONT_BOLD),
                "-pointsize", "68",
                "-annotate", f"+56+{150 + idx * 76}", line,
            ] for idx, line in enumerate(wrap_lines(title, 20, max_lines=2))), [])),
            *(sum(([
                "-fill", "#dbe6ef", "-font", str(FONT_REGULAR),
                "-pointsize", "32", "-annotate", f"+56+{320 + idx * 42}", line,
            ] for idx, line in enumerate(subtitle_lines[:2])), [])),
            "-fill", "#0c1118", "-draw", "roundrectangle 40,430 1160,590 28,28",
            "-fill", "#ffd68a", "-font", str(FONT_BOLD), "-pointsize", "34",
            "-annotate", "+240+466", footer,
            "-fill", "#f3f4f6", "-font", str(FONT_REGULAR), "-pointsize", "26",
            "-annotate", "+240+516", site.get("sharingTagline", "Guess the price. Unlock the deal."),
            "-fill", "#dbe6ef", "-font", str(FONT_REGULAR), "-pointsize", "22",
            "-annotate", "+56+606", caption,
            str(tmp),
        ])
        run_convert([
            str(tmp), str(qr_path),
            "-geometry", "+56+444",
            "-composite",
            str(path),
        ])
        if tmp.exists():
            tmp.unlink()
        return

    image_path = ensure_square_card_image(item.get("image"))
    title_lines = wrap_lines(item.get("name", title), 20, max_lines=2)
    category_line = item.get("category", "Item")
    reference_line = f"{site['strings']['referencePriceLabel']}: {money(item.get('referencePrice', 0), site)}"
    actual_price = item.get("actualPrice")
    if actual_price is None:
        actual_line = display_status(item, site)
    else:
        actual_line = f"{site['strings'].get('actualPriceLabel', 'Actual price')}: {money(actual_price, site)}"

    run_convert([
        "-size", "1200x630", "xc:#eaeded",
        "-fill", "#f3a847", "-draw", "rectangle 0,0 1200,96",
        "-fill", "#131a22", "-font", str(FONT_BOLD), "-gravity", "northwest",
        "-pointsize", "40", "-annotate", "+56+28", top_title,
        "-fill", "white", "-draw", "roundrectangle 40,130 1160,590 28,28",
        "-fill", "#f5f7f9", "-draw", "roundrectangle 68,174 488,594 22,22",
        *(sum(([
            "-fill", "#131a22",
            "-font", str(FONT_BOLD),
            "-pointsize", "46",
            "-annotate", f"+540+{190 + idx * 54}", line,
        ] for idx, line in enumerate(title_lines)), [])),
        "-fill", "#5d6b7a", "-font", str(FONT_REGULAR),
        "-pointsize", "28", "-annotate", "+540+316", category_line,
        "-stroke", "#d5d9dd", "-strokewidth", "2", "-draw", "line 540,340 1096,340",
        "-fill", "#5d6b7a", "-stroke", "none", "-font", str(FONT_BOLD),
        "-pointsize", "28", "-annotate", "+540+368", reference_line,
        "-fill", "#b12704", "-font", str(FONT_BOLD),
        "-pointsize", "40", "-annotate", "+780+512", actual_line,
        str(tmp),
    ])
    run_convert([
        str(tmp), str(image_path),
        "-geometry", "+68+174",
        "-composite",
        str(qr_path),
        "-geometry", "+540+404",
        "-composite",
        str(path),
    ])
    if tmp.exists():
        tmp.unlink()


def display_status(item: dict, site: dict) -> str:
    status = str(item.get("status", "available"))
    strings = site["strings"]
    if status == "available":
        return strings["statusAvailable"]
    if status == "pending":
        return strings["statusPending"]
    if status == "sold":
        return strings["statusSold"]
    return strings["statusUnavailable"]


def compute_generated_price(item: dict) -> float | None:
    actual = item.get("actualPrice")
    reference = item.get("referencePrice")
    if actual is None or reference is None:
        return None
    actual = float(actual)
    reference = float(reference)
    if reference <= actual:
        return round(actual, 2)
    digest = hashlib.sha1(f"public-price::{item.get('id','')}".encode("utf-8")).hexdigest()[:8]
    ratio = int(digest, 16) / 0xFFFFFFFF
    value = actual + (reference - actual) * ratio
    return round(value)


def translate_item(item: dict, lang: str) -> dict:
    out = copy.deepcopy(item)
    if lang != "en":
        out["name"] = ITEM_ZH.get(item["id"], {}).get("name", item["name"])
        out["description"] = ITEM_ZH.get(item["id"], {}).get("description", item.get("description", ""))
        out["pickupNotes"] = ITEM_ZH.get(item["id"], {}).get("pickupNotes", item.get("pickupNotes", ""))
        out["category"] = CATEGORY_ZH.get(item.get("category", ""), item.get("category", ""))
        out["condition"] = CONDITION_ZH.get(item.get("condition", ""), item.get("condition", ""))
    out["generatedPrice"] = compute_generated_price(item)
    return out

def localize_catalog(catalog: dict, lang: str) -> dict:
    site_base = copy.deepcopy(catalog["site"])
    locale_cfg = SITE_I18N[lang]
    site_base["subtitle"] = locale_cfg["subtitle"]
    site_base["defaultDescription"] = locale_cfg["defaultDescription"]
    site_base["sharingTagline"] = locale_cfg["sharingTagline"]
    site_base["deliveryNote"] = locale_cfg["deliveryNote"]
    site_base["pickupNote"] = locale_cfg["pickupNote"]
    site_base["locale"] = lang
    site_base["htmlLang"] = locale_cfg["htmlLang"]
    site_base["numberLocale"] = locale_cfg["numberLocale"]
    site_base["strings"] = locale_cfg["strings"]
    public_base = site_base.get("publicUrl", site_base.get("baseUrl", "https://nesbitt-bot.github.io/Congo")).rstrip("/")
    localized_items = []
    for item in catalog["items"]:
        out = translate_item(item, lang)
        out["publicItemUrl"] = f"{public_base}/{lang}/item/{item['id']}/?mode=plain"
        out["qrImage"] = f"https://api.qrserver.com/v1/create-qr-code/?size=120x120&margin=0&data={quote_plus(out['publicItemUrl'])}"
        localized_items.append(out)
    return {
        "site": site_base,
        "items": localized_items,
    }


def alt_links(path_suffix: str) -> dict[str, str]:
    base = "https://nesbitt-bot.github.io/Congo"
    normalized = path_suffix.strip("/")
    en_suffix = f"/en/{normalized}".rstrip("/") if normalized else "/en"
    zh_suffix = f"/zh/{normalized}".rstrip("/") if normalized else "/zh"
    return {
        "en": base + en_suffix + ("/" if normalized else "/"),
        "zh": base + zh_suffix + ("/" if normalized else "/"),
    }


def topbar_html(*, asset_root: str, page_root: str, site: dict, page: str, switch_en: str, switch_zh: str, current_lang: str) -> str:
    s = site["strings"]

    def nav_link(href: str, label: str, icon: str, key: str) -> str:
        active = " active" if page == key else ""
        return f'<a class="nav-link{active}" href="{href}"><span>{icon}</span><span>{escape(label)}</span></a>'

    return f"""
    <header class=\"topbar\">
      <div class=\"topbar-inner\">
        <a class=\"brand-lockup\" href=\"{page_root}\">
          <span class=\"brand-mark\">{escape(str(site.get('logoEmoji', 'CO')))}</span>
          <span class=\"brand-copy\">
            <strong>{escape(site.get('title', 'Congo'))}</strong>
            <span>{escape(s['brandTagline'])}</span>
          </span>
        </a>
        <div class=\"search-shell\">
          <input id=\"global-search\" type=\"search\" placeholder=\"{escape(s['searchPlaceholder'])}\" />
          <button id=\"global-search-button\" type=\"button\" aria-label=\"Search\">⌕</button>
        </div>
        <nav class=\"primary-links\" aria-label=\"Primary\">
          {nav_link(page_root + 'about/', s['aboutNav'], 'ℹ', 'about')}
        </nav>
        <a class=\"cart-link compact\" href=\"{page_root}checkout/\" aria-label=\"{escape(s['cartNav'])}\">
          <span class=\"cart-icon\">🛒</span>
          <span class=\"cart-count-inline\"><span data-cart-count>0</span></span>
        </a>
        <div class="language-switch">
          <select class="language-select language-select-flags" data-language-switch aria-label="{escape(s['langSwitchLabel'])}">
            <option value="{switch_en}" {"selected" if current_lang == "en" else ""}>🇺🇸 EN</option>
            <option value="{switch_zh}" {"selected" if current_lang == "zh" else ""}>🇨🇳 中文</option>
          </select>
        </div>
      </div>
      <div class=\"nav-secondary\">
        <div class=\"nav-secondary-inner\" id=\"category-chips\"></div>
      </div>
    </header>
    """


def mobile_footer_html(*, page_root: str, page: str, site: dict) -> str:
    s = site["strings"]

    def tab(href: str, label: str, icon: str, key: str) -> str:
        active = " active" if page == key else ""
        return f'<a class="mobile-tab{active}" href="{href}"><span class="mobile-tab-icon">{icon}</span><span class="mobile-tab-label">{escape(label)}</span></a>'

    return f"""
    <nav class=\"mobile-footer-nav\" aria-label=\"Mobile footer\">
      <div class=\"mobile-footer-nav-inner\">
        {tab(page_root, s['homeNav'], '⌂', 'index')}
        {tab(page_root + 'checkout/', s['cartNav'], '🛒', 'checkout')}
        {tab(page_root + 'about/', s['aboutNav'], 'ℹ', 'about')}
      </div>
    </nav>
    """


def html_shell(*, target_dir: Path, variant_base: Path, lang: str, page: str, path_suffix: str, title: str, description: str, image_url: str, body: str, site: dict, extra_script: str = "") -> str:
    asset_root = rel_prefix(target_dir, DIST)
    page_root = rel_prefix(target_dir, variant_base)
    data_url = page_root + "data/catalog.json"
    alts = alt_links(path_suffix)
    page_lang = site.get("htmlLang", "en")
    site_title = escape(site.get("title", "Congo"))
    payload = json.dumps(site, ensure_ascii=False)
    canonical = alts[lang]
    return f"""<!doctype html>
<html lang=\"{escape(page_lang)}\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>{escape(title)}</title>
    <meta name=\"description\" content=\"{escape(description)}\" />
    <meta property=\"og:type\" content=\"website\" />
    <meta property=\"og:title\" content=\"{escape(title)}\" />
    <meta property=\"og:description\" content=\"{escape(description)}\" />
    <meta property=\"og:url\" content=\"{escape(canonical)}\" />
    <meta property=\"og:image\" content=\"{escape(image_url)}\" />
    <meta property=\"og:site_name\" content=\"{site_title}\" />
    <meta name=\"twitter:card\" content=\"summary_large_image\" />
    <meta name=\"twitter:title\" content=\"{escape(title)}\" />
    <meta name=\"twitter:description\" content=\"{escape(description)}\" />
    <meta name=\"twitter:image\" content=\"{escape(image_url)}\" />
    <link rel=\"canonical\" href=\"{escape(canonical)}\" />
    <link rel=\"alternate\" hreflang=\"en\" href=\"{escape(alts['en'])}\" />
    <link rel=\"alternate\" hreflang=\"zh-CN\" href=\"{escape(alts['zh'])}\" />
    <link rel=\"icon\" href=\"{asset_root}assets/favicon.svg\" type=\"image/svg+xml\" />
    <link rel=\"stylesheet\" href=\"{asset_root}assets/styles.css\" />
  </head>
  <body data-page=\"{page}\" class=\"has-mobile-footer\">
    {topbar_html(asset_root=asset_root, page_root=page_root, site=site, page=page, switch_en=alts['en'], switch_zh=alts['zh'], current_lang=lang)}
    {body}
    <footer class=\"footer\">
      <div class=\"footer-inner\">
        <div><strong>{site_title}</strong> · {escape(site.get('subtitle', ''))}</div>
        <div>{escape(site.get('deliveryNote', ''))}</div>
        <div><a href=\"{escape(site.get('githubRepoUrl', 'https://github.com/Nesbitt-bot/Congo'))}\">{escape(site.get('githubRepoUrl', 'https://github.com/Nesbitt-bot/Congo'))}</a></div>
      </div>
    </footer>
    {mobile_footer_html(page_root=page_root, page=page, site=site)}
    <script>window.CONGO_ASSET_ROOT = {json.dumps(asset_root)}; window.CONGO_PAGE_ROOT = {json.dumps(page_root)}; window.CONGO_DATA_URL = {json.dumps(data_url)}; window.CONGO_SITE = {payload}; window.CONGO_PAGE_LANG = {json.dumps(lang)}; {extra_script}</script>
    <script src=\"{asset_root}assets/app.js\"></script>
  </body>
</html>
"""


def index_body(site: dict) -> str:
    s = site["strings"]
    return f"""
    <main class=\"section\">
      <div class=\"mode-chooser panel\" id=\"mode-chooser\">
        <div>
          <strong>{escape(s['modeChooserTitle'])}</strong>
          <p class=\"muted\">{escape(s['modeChooserBody'])}</p>
        </div>
        <div class=\"inline-actions\">
          <a id=\"mode-plain-link\" class=\"btn-amazon\" href=\"?mode=plain\">{escape(s['modePlainButton'])}</a>
          <a id=\"mode-guess-link\" class=\"btn-ghost\" href=\"?mode=guess\">{escape(s['modeGuessButton'])}</a>
        </div>
      </div>
      <div class=\"section-header\">
        <div>
          <h1>{escape(s['availableItemsTitle'])}</h1>
          <p>{escape(s['availableItemsDesc'])}</p>
        </div>
      </div>
      <div class=\"catalog-toolbar panel\">
        <label class=\"toggle-row\">
          <input id=\"hide-sold-toggle\" type=\"checkbox\" checked />
          <span>{escape(s['hideSoldOut'])}</span>
        </label>
        <div class=\"muted\" id=\"catalog-count\"></div>
      </div>
      <div id=\"page-error\" class=\"status-box bad hide\"></div>
      <div id=\"catalog-grid\" class=\"catalog-grid\"></div>
      <div id=\"catalog-sentinel\" class=\"catalog-sentinel muted\">{escape(s['loadingMore'])}</div>
    </main>
    """


def item_body(site: dict, item: dict, asset_root: str) -> str:
    s = site["strings"]
    category = escape(item.get("category", "Item"))
    condition = escape(item.get("condition", "Used"))
    reference_link = escape(item.get("referenceLink", "#"))
    reference_price = escape(money(item.get("referencePrice", 0), site))
    description = escape(item.get("description", ""))
    pickup_notes = escape(item.get("pickupNotes", ""))
    images = item.get("images") or [item.get("image", f"assets/{PLACEHOLDER_NAME}")]
    images = [img for img in images if img] or [f"assets/{PLACEHOLDER_NAME}"]
    thumb_buttons = ""
    if len(images) > 1:
        thumb_buttons = "".join(
            f'<button type="button" class="gallery-thumb{" active" if idx == 0 else ""}" data-gallery-image="{escape(img)}" aria-label="View photo {idx + 1}"><img src="{escape(rel_asset(img, asset_root))}" alt="{escape(item.get("name", "Item image"))} photo {idx + 1}" onerror="this.src=\'{asset_root}assets/{PLACEHOLDER_NAME}\'" /></button>'
            for idx, img in enumerate(images)
        )
    quantity = int(item.get("quantity", 1))
    status_text = escape(display_status(item, site))
    badge_class = "green" if str(item.get("status")) == "available" else ""
    earliest_pickup = escape(item.get("earliestPickupDate", ""))
    latest_pickup = escape(item.get("latestPickupDate", ""))
    latest_pickup_line = f'<li><span class="spec-label">{escape(s["latestPickupLabel"])}</span><span>{latest_pickup}</span></li>' if latest_pickup else ''
    gallery_strip = f'<div class="gallery-strip">{thumb_buttons}</div>' if thumb_buttons else ''
    return f"""
    <main class=\"item-page\">
      <section class=\"panel media-panel\">
        <div class=\"media-frame\">
          <img id=\"item-main-image\" src=\"{escape(rel_asset(images[0], asset_root))}\" alt=\"{escape(item.get('name', 'Item image'))}\" onerror=\"this.src='{asset_root}assets/{PLACEHOLDER_NAME}'\" />
        </div>
        {gallery_strip}
      </section>
      <section class=\"item-meta\">
        <div class=\"panel detail-panel\">
          <div class=\"badge-row\" style=\"position:static;justify-content:flex-start;margin-bottom:10px\">
            <span class=\"badge gold\">{category}</span>
            <span class=\"badge\">{condition}</span>
            <span class=\"badge {badge_class}\">{status_text}</span>
          </div>
          <h1>{escape(item.get('name', 'Untitled item'))}</h1>
          <p class=\"muted\">{description}</p>
          <ul class=\"spec-list\">
            <li><span class=\"spec-label\">{escape(s['referencePriceLabel'])}</span><span><a class=\"reference-link\" href=\"{reference_link}\" target=\"_blank\" rel=\"noreferrer\">{reference_price}</a></span></li>
            <li><span class=\"spec-label\">{escape(s['quantityLabel'])}</span><span>{quantity}</span></li>
            <li><span class=\"spec-label\">{escape(s['earliestPickupLabel'])}</span><span>{earliest_pickup or escape(s['availableNow'])}</span></li>
            {latest_pickup_line}
            <li><span class=\"spec-label\">{escape(s['pickupNoteLabel'])}</span><span>{pickup_notes or escape(site.get('pickupNote', ''))}</span></li>
          </ul>
        </div>
        <div class=\"panel guess-panel\">
          <h2 class=\"block-title\">{escape(s['unlockTitle'])}</h2>
          <p class=\"muted\">{escape(s['guessInputPlaceholder']) if 'guessInputPlaceholder' in s else escape(s['unlockSubtitle'])}</p>
          <div class=\"guess-box\">
            <div class=\"status-box info\" id=\"guess-status\">{escape(s['offersLeft'].format(count=3))}</div>
            <div class=\"guess-input-row\">
              <input id=\"guess-input\" type=\"number\" min=\"0\" step=\"0.01\" placeholder=\"{escape(s['guessInputPlaceholder'])}\" />
              <button id=\"guess-button\" class=\"btn-amazon\">{escape(s['guessButton'])}</button>
            </div>
            <div class=\"small-note\" id=\"hidden-price-hint\">{escape(s['generatedNegotiablePrice'].format(price=money(item.get('generatedPrice') or item.get('referencePrice') or 0, site))) if item.get('generatedPrice') else escape(s['hiddenCheckoutPrice'])}</div>
            <div class=\"reveal-price hide\" id=\"reveal-price\">{escape(s['unlockTitle'])}: <span data-offer-price></span></div>
            <div class=\"inline-actions hide\" id=\"unlock-actions\">
              <button id=\"add-to-cart\" class=\"btn-amazon\">{escape(s['addToCart'])}</button>
              <button id=\"buy-now\" class=\"btn-secondary\">{escape(s['checkoutNow'])}</button>
            </div>
          </div>
        </div>
      </section>
    </main>
    """


def checkout_body(site: dict) -> str:
    s = site["strings"]
    threshold = escape(money(site.get("freeDeliveryThreshold", 0), site))
    contact_email = escape(site.get("contactEmail", "your-email@example.com"))

    if site.get("locale") == "zh":
        public = site.get("publicUrl", site.get("baseUrl", "https://nesbitt-bot.github.io/Congo")).rstrip("/")
        wechat_image = escape(f"{public}/{str(site.get('wechatContactImage', 'media/wechat-contact-qr.jpg')).lstrip('/')}")
        wechat_label = escape(site.get("wechatContactLabel", "微信"))
        return f"""
    <main class="checkout-page">
      <section class="cart-panel panel">
        <div class="section-header" style="margin-bottom:18px">
          <div>
            <h1>{escape(s['checkoutTitle'])}</h1>
            <p>{escape(s['checkoutDesc'])}</p>
          </div>
          <button id="clear-cart" class="btn-ghost">{escape(s['clearCart'])}</button>
        </div>
        <div id="page-error" class="status-box bad hide"></div>
        <div id="cart-list" class="cart-list"></div>
      </section>
      <aside class="summary-card checkout-card">
        <h2 class="block-title">{escape(s['orderSummary'])}</h2>
        <div class="checkout-summary-rows" style="margin:16px 0">
          <div class="checkout-summary-row"><span>{escape(s['itemsLabel'])}</span><strong id="summary-count">0</strong></div>
          <div class="checkout-summary-row"><span>{escape(s['totalLabel'])}</span><strong id="summary-total">$0</strong></div>
        </div>
        <div class="progress"><span id="delivery-progress" style="width:0%"></span></div>
        <div id="delivery-message" class="status-box info" style="margin-top:12px">{escape(s['deliveryNeedMore'].format(amount=threshold))}</div>
        <div class="wechat-contact-card">
          <h3>微信联系</h3>
          <p class="muted">下单后请直接扫码添加微信，备注想要的商品、取货时间和联系方式。</p>
          <img class="wechat-contact-image" src="{wechat_image}" alt="微信联系二维码" />
          <div class="wechat-contact-id">{wechat_label}</div>
        </div>
      </aside>
    </main>
    """

    return f"""
    <main class="checkout-page">
      <section class="cart-panel panel">
        <div class="section-header" style="margin-bottom:18px">
          <div>
            <h1>{escape(s['checkoutTitle'])}</h1>
            <p>{escape(s['checkoutDesc'])}</p>
          </div>
          <button id="clear-cart" class="btn-ghost">{escape(s['clearCart'])}</button>
        </div>
        <div id="page-error" class="status-box bad hide"></div>
        <div id="cart-list" class="cart-list"></div>
      </section>
      <aside class="summary-card checkout-card">
        <h2 class="block-title">{escape(s['orderSummary'])}</h2>
        <div class="checkout-summary-rows" style="margin:16px 0">
          <div class="checkout-summary-row"><span>{escape(s['itemsLabel'])}</span><strong id="summary-count">0</strong></div>
          <div class="checkout-summary-row"><span>{escape(s['totalLabel'])}</span><strong id="summary-total">$0</strong></div>
        </div>
        <div class="progress"><span id="delivery-progress" style="width:0%"></span></div>
        <div id="delivery-message" class="status-box info" style="margin-top:12px">{escape(s['deliveryNeedMore'].format(amount=threshold))}</div>
        <p class="small-note">{escape(s['checkoutAddressedTo'].format(email=site.get('contactEmail', '')))}</p>
        <form id="checkout-form" class="checkout-form">
          <div class="form-grid">
            <input name="name" placeholder="{escape(s['yourName'])}" />
            <input name="email" type="email" placeholder="{escape(s['yourEmail'])}" />
            <input name="phone" placeholder="{escape(s['yourPhone'])}" />
            <input name="when" placeholder="{escape(s['preferredTime'])}" />
          </div>
          <select name="deliveryMode">
            <option>{escape(s['pickupOption'])}</option>
            <option>{escape(s['localDeliveryOption'])}</option>
            <option>{escape(s['eitherWorksOption'])}</option>
          </select>
          <input name="address" placeholder="{escape(s['pickupPoint'])}" />
          <textarea name="notes" placeholder="{escape(s['notesPlaceholder'])}"></textarea>
          <div class="inline-actions">
            <button type="button" id="copy-email" class="btn-amazon">{escape(s['copyEmailText'])}</button>
            <a id="open-mailto" class="btn-secondary" href="mailto:{contact_email}">{escape(s['openEmailDraft'])}</a>
          </div>
        </form>
      </aside>
    </main>
    """


def about_body(site: dict) -> str:
    s = site["strings"]
    threshold = escape(money(site.get("freeDeliveryThreshold", 0), site))
    email = f"<strong>{escape(site.get('contactEmail', ''))}</strong>"
    items = "".join(f"<li>{escape(line.format(threshold=threshold, email=site.get('contactEmail', '')))}</li>" for line in s["howItWorksItems"])
    items = items.replace(escape(site.get('contactEmail', '')), email)
    return f"""
    <main class=\"section\">
      <div class=\"about-stack\">
        <section class=\"about-panel panel\">
          <h1 class=\"block-title\">{escape(s['aboutHeroTitle'])}</h1>
          <p class=\"muted\">{escape(s['aboutHeroBody'])}</p>
        </section>
        <section class=\"about-panel panel\">
          <h2 class=\"block-title\">{escape(s['howItWorksTitle'])}</h2>
          <ul class=\"about-list\">{items}</ul>
        </section>
      </div>
    </main>
    """


def summary_slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalized).strip("-").lower()
    return slug or "other"


def summary_copy_media(source_path: str, target: Path) -> Path:
    source = ROOT / str(source_path).lstrip("/")
    if not source.exists():
        source = DIST / str(source_path).lstrip("/")
    if not source.exists():
        source = DIST / "assets" / PLACEHOLDER_NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target


def summary_contact_lines(site: dict, lang: str, *, image_rel: str | None = None) -> list[str]:
    if lang == "zh":
        label = site.get("wechatContactLabel", "微信")
        lines = [f"微信联系：{label}", ""]
        if image_rel:
            lines.extend([f"![微信联系二维码]({image_rel})", ""])
        return lines
    email = site.get("contactEmail", "")
    return [f"Contact email: <{email}>", ""] if email else []


def summary_contact_text_lines(site: dict, lang: str, *, image_rel: str | None = None) -> list[str]:
    if lang == "zh":
        label = site.get("wechatContactLabel", "微信")
        return [f"微信联系：{label}", ""]
    email = site.get("contactEmail", "")
    return [f"Contact email: {email}", ""] if email else []


def grouped_summary_items(catalog: dict, lang: str) -> tuple[dict, list[tuple[str, str, list[dict]]]]:
    localized = localize_catalog(catalog, lang)
    site = localized["site"]
    grouped: dict[str, dict] = {}
    for original, item in zip(catalog["items"], localized["items"]):
        if item.get("status") == "sold":
            continue
        key = original.get("category", "Other")
        bucket = grouped.setdefault(key, {"label": item.get("category", key), "items": []})
        bucket["items"].append(item)
    ordered = []
    for key in sorted(grouped.keys(), key=lambda value: grouped[value]["label"]):
        ordered.append((key, grouped[key]["label"], grouped[key]["items"]))
    return site, ordered


def summary_lines_for_catalog(catalog: dict, lang: str, *, items: list[dict] | None = None, category_label: str | None = None, contact_image_rel: str | None = None) -> str:
    site = localize_catalog(catalog, lang)["site"]
    public = site.get("publicUrl", site.get("baseUrl", "https://nesbitt-bot.github.io/Congo")).rstrip("/")
    pickup = site.get("pickupAddress", "")
    is_zh = lang == "zh"
    intro = f"出二手 自取 {pickup}" if is_zh else f"Second-hand for sale · Pickup at {pickup}"
    site_url = f"{public}/{lang}/?mode=plain"
    site_line = f"最新页面：{site_url}" if is_zh else f"Latest update: {site_url}"
    sections = [intro, site_line, ""]
    if category_label:
        sections.append(f"# {category_label}")
        sections.append("")
    sections.extend(summary_contact_lines(site, lang, image_rel=contact_image_rel))
    for item in items or []:
        price = item.get("actualPrice")
        price_label = (f"${int(price) if float(price).is_integer() else price}" if price is not None else ("待定" if is_zh else "Price pending"))
        item_url = f"{public}/{lang}/item/{item['id']}/?mode=plain"
        image_path = item.get("summaryImageRel") or item.get("image") or (item.get("images") or ["assets/placeholder.png"])[0]
        sections.append(f"## [{item['name']}]({item_url}) ({price_label})")
        sections.append("")
        sections.append((f"最早可取：{item.get('earliestPickupDate', '')}" if is_zh else f"Earliest available: {item.get('earliestPickupDate', '')}"))
        if item.get('latestPickupDate'):
            sections.append((f"最晚可取：{item.get('latestPickupDate')}" if is_zh else f"Latest available: {item.get('latestPickupDate')}"))
        if item.get('pickupNotes'):
            sections.append((f"附加信息：{item.get('pickupNotes')}" if is_zh else f"Additional info: {item.get('pickupNotes')}"))
        sections.append("")
        sections.append(f"![{item['name']}]({image_path})")
        sections.append("")
    return "\n".join(sections).strip() + "\n"


def summary_text_for_catalog(catalog: dict, lang: str, *, items: list[dict] | None = None, category_label: str | None = None, contact_image_rel: str | None = None) -> str:
    site = localize_catalog(catalog, lang)["site"]
    public = site.get("publicUrl", site.get("baseUrl", "https://nesbitt-bot.github.io/Congo")).rstrip("/")
    pickup = site.get("pickupAddress", "")
    is_zh = lang == "zh"
    intro = f"出二手 自取 {pickup}" if is_zh else f"Second-hand for sale · Pickup at {pickup}"
    site_url = f"{public}/{lang}/?mode=plain"
    site_line = f"最新页面：{site_url}" if is_zh else f"Latest update: {site_url}"
    sections = [intro, site_line, ""]
    if category_label:
        sections.append(f"Category: {category_label}" if not is_zh else f"分类：{category_label}")
        sections.append("")
    sections.extend(summary_contact_text_lines(site, lang, image_rel=contact_image_rel))
    for item in items or []:
        price = item.get("actualPrice")
        price_label = (f"${int(price) if float(price).is_integer() else price}" if price is not None else ("待定" if is_zh else "Price pending"))
        item_url = f"{public}/{lang}/item/{item['id']}/?mode=plain"
        sections.append(f"{item['name']} — {price_label}")
        sections.append((f"最早可取：{item.get('earliestPickupDate', '')}" if is_zh else f"Earliest available: {item.get('earliestPickupDate', '')}"))
        if item.get('latestPickupDate'):
            sections.append((f"最晚可取：{item.get('latestPickupDate')}" if is_zh else f"Latest available: {item.get('latestPickupDate')}"))
        if item.get('pickupNotes'):
            sections.append((f"附加信息：{item.get('pickupNotes')}" if is_zh else f"Additional info: {item.get('pickupNotes')}"))
        sections.append("")
    return "\n".join(sections).strip() + "\n"


def summary_index_lines(catalog: dict, lang: str, grouped: list[tuple[str, str, list[dict]]], *, contact_image_rel: str | None = None, extension: str = "md") -> str:
    site = localize_catalog(catalog, lang)["site"]
    public = site.get("publicUrl", site.get("baseUrl", "https://nesbitt-bot.github.io/Congo")).rstrip("/")
    pickup = site.get("pickupAddress", "")
    is_zh = lang == "zh"
    intro = f"出二手 自取 {pickup}" if is_zh else f"Second-hand for sale · Pickup at {pickup}"
    site_url = f"{public}/{lang}/?mode=plain"
    site_line = f"最新页面：{site_url}" if is_zh else f"Latest update: {site_url}"
    if extension == "md":
        title = "# 分类汇总" if is_zh else "# Category summaries"
        sections = [intro, site_line, "", title, ""]
        sections.extend(summary_contact_lines(site, lang, image_rel=contact_image_rel))
        for category_key, category_label, items in grouped:
            slug = summary_slug(category_key)
            rel_path = f"./{lang}/{slug}.md"
            count = len(items)
            label = f"{count} 件" if is_zh else f"{count} item{'s' if count != 1 else ''}"
            sections.append(f"- [{category_label}]({rel_path}) ({label})")
        sections.append("")
        return "\n".join(sections)
    title = "分类汇总" if is_zh else "Category summaries"
    sections = [intro, site_line, "", title, ""]
    sections.extend(summary_contact_text_lines(site, lang, image_rel=contact_image_rel))
    for category_key, category_label, items in grouped:
        count = len(items)
        label = f"{count} 件" if is_zh else f"{count} item{'s' if count != 1 else ''}"
        sections.append(f"- {category_label} ({label})")
    sections.append("")
    return "\n".join(sections)


def write_summary_files(catalog: dict) -> None:
    summary_dir = ROOT / "summary"
    media_dir = summary_dir / "media"
    summary_dir.mkdir(parents=True, exist_ok=True)
    if media_dir.exists():
        shutil.rmtree(media_dir)
    media_dir.mkdir(parents=True, exist_ok=True)
    for lang in ["en", "zh"]:
        lang_dir = summary_dir / lang
        lang_dir.mkdir(parents=True, exist_ok=True)
        for stale in lang_dir.glob("*.md"):
            stale.unlink()
        for stale in lang_dir.glob("*.txt"):
            stale.unlink()
        site, grouped = grouped_summary_items(catalog, lang)
        contact_rel_root = None
        if lang == "zh":
            contact_name = Path(str(site.get("wechatContactImage", "media/wechat-contact-qr.jpg"))).name or "wechat-contact-qr.jpg"
            contact_target = summary_copy_media(str(site.get("wechatContactImage", "media/wechat-contact-qr.jpg")), media_dir / "contact" / contact_name)
            contact_rel_root = Path(shutil.os.path.relpath(contact_target, summary_dir)).as_posix()
        for category_key, category_label, items in grouped:
            slug = summary_slug(category_key)
            prepared_items = []
            for item in items:
                clone = dict(item)
                image_source = item.get("image") or (item.get("images") or ["assets/placeholder.png"])[0]
                source_suffix = Path(str(image_source)).suffix or ".jpg"
                image_target = summary_copy_media(image_source, media_dir / slug / f"{item['id']}{source_suffix}")
                clone["summaryImageRel"] = Path(shutil.os.path.relpath(image_target, lang_dir)).as_posix()
                prepared_items.append(clone)
            contact_rel_lang = Path(shutil.os.path.relpath(media_dir / "contact" / Path(str(site.get("wechatContactImage", "media/wechat-contact-qr.jpg"))).name, lang_dir)).as_posix() if lang == "zh" else None
            (lang_dir / f"{slug}.md").write_text(
                summary_lines_for_catalog(catalog, lang, items=prepared_items, category_label=category_label, contact_image_rel=contact_rel_lang),
                encoding="utf-8",
            )
            (lang_dir / f"{slug}.txt").write_text(
                summary_text_for_catalog(catalog, lang, items=prepared_items, category_label=category_label, contact_image_rel=contact_rel_lang),
                encoding="utf-8",
            )
        (summary_dir / f"summary.{lang}.md").write_text(summary_index_lines(catalog, lang, grouped, contact_image_rel=contact_rel_root, extension="md"), encoding="utf-8")
        (summary_dir / f"summary.{lang}.txt").write_text(summary_index_lines(catalog, lang, grouped, contact_image_rel=contact_rel_root, extension="txt"), encoding="utf-8")


def write_catalog_files(catalog: dict) -> None:
    (DIST / "data" / "catalog.json").write_text(json.dumps(localize_catalog(catalog, "en"), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for lang in ["en", "zh"]:
        target = DIST / lang / "data"
        target.mkdir(parents=True, exist_ok=True)
        localized = localize_catalog(catalog, lang)
        (target / "catalog.json").write_text(json.dumps(localized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def variant_root(lang_variant: str) -> Path:
    if lang_variant == "root-en":
        return DIST
    return DIST / lang_variant


def variant_lang(lang_variant: str) -> str:
    return "en" if lang_variant in {"root-en", "en"} else "zh"


def public_base(lang_variant: str, site: dict) -> str:
    base = site.get("baseUrl", "https://nesbitt-bot.github.io/Congo").rstrip("/")
    if lang_variant == "root-en":
        return base
    return f"{base}/{lang_variant}"


def poster_path(lang_variant: str, item_id: str | None = None) -> str:
    if lang_variant == "root-en":
        return f"/og/{item_id}.png" if item_id else "/og/default.png"
    return f"/og/{lang_variant}/{item_id}.png" if item_id else f"/og/{lang_variant}/default.png"


def write_posters_for_variant(catalog: dict, lang_variant: str) -> None:
    lang = variant_lang(lang_variant)
    localized = localize_catalog(catalog, lang)
    site = localized["site"]
    public = public_base(lang_variant, site)
    out_dir = OG if lang_variant == "root-en" else OG / lang_variant
    out_dir.mkdir(parents=True, exist_ok=True)
    create_poster_png(
        out_dir / "default.png",
        site=site,
        lang=lang,
        title=site["strings"]["posterDefaultTitle"],
        subtitle_lines=wrap_lines(site.get("defaultDescription", ""), 28, max_lines=2),
        footer=site.get("sharingTagline", "Guess the price. Unlock the deal."),
        qr_target=public + ("/" if not public.endswith("/") else ""),
    )
    for item in localized["items"]:
        create_poster_png(
            out_dir / f"{item['id']}.png",
            site=site,
            lang=lang,
            title=item.get("name", "Untitled item"),
            subtitle_lines=wrap_lines(site["strings"]["posterCategoryLine"].format(category=item.get("category", "Item")), 28, max_lines=2),
            footer=f"{site['strings']['referencePriceLabel']}: {money(item.get('referencePrice', 0), site)}",
            qr_target=f"{public}/item/{item['id']}/",
            item=item,
        )


def write_root_redirect() -> None:
    (DIST / "index-redirect.html").write_text("", encoding="utf-8")


def page_title(site: dict, page: str, item: dict | None = None) -> str:
    s = site["strings"]
    if page == "index":
        return f"{site.get('title', 'Congo')} · {s['availableItemsTitle']}"
    if page == "about":
        return f"{s['aboutNav']} · {site.get('title', 'Congo')}"
    if page == "checkout":
        return f"{s['checkoutTitle']} · {site.get('title', 'Congo')}"
    if item:
        return f"{item.get('name', 'Item')} · {site.get('title', 'Congo')}"
    return site.get('title', 'Congo')


def write_pages_for_variant(catalog: dict, lang_variant: str) -> None:
    lang = variant_lang(lang_variant)
    localized = localize_catalog(catalog, lang)
    site = localized["site"]
    base_dir = variant_root(lang_variant)
    base_dir.mkdir(parents=True, exist_ok=True)
    public = public_base(lang_variant, site)

    pages = [
        (base_dir, "index", "", index_body(site), site.get("defaultDescription", ""), None),
        (base_dir / "about", "about", "about", about_body(site), site["strings"]["aboutHeroBody"], None),
        (base_dir / "checkout", "checkout", "checkout", checkout_body(site), site["strings"]["checkoutDesc"], None),
    ]

    for target_dir, page, suffix, body, description, item in pages:
        target_dir.mkdir(parents=True, exist_ok=True)
        image_url = site.get("baseUrl", "").rstrip("/") + poster_path(lang_variant)
        html = html_shell(
            target_dir=target_dir,
            variant_base=base_dir,
            lang=lang,
            page=page,
            path_suffix=suffix,
            title=page_title(site, page),
            description=description,
            image_url=image_url,
            body=body,
            site=site,
        )
        (target_dir / "index.html").write_text(html, encoding="utf-8")

    for item in localized["items"]:
        item_dir = base_dir / "item" / item["id"]
        item_dir.mkdir(parents=True, exist_ok=True)
        extra_script = f"window.CONGO_CURRENT_ITEM = {json.dumps(item, ensure_ascii=False)};"
        description = f"{item.get('category', 'Item')} · {site['strings']['referencePriceLabel']} {money(item.get('referencePrice', 0), site)}"
        image_url = site.get("baseUrl", "").rstrip("/") + poster_path(lang_variant, item["id"])
        html = html_shell(
            target_dir=item_dir,
            variant_base=base_dir,
            lang=lang,
            page="item",
            path_suffix=f"item/{item['id']}",
            title=page_title(site, "item", item=item),
            description=description,
            image_url=image_url,
            body=item_body(site, item, rel_prefix(item_dir, DIST)),
            site=site,
            extra_script=extra_script,
        )
        (item_dir / "index.html").write_text(html, encoding="utf-8")


def write_support_assets() -> None:
    ensure_fonts()
    create_favicon(ASSETS / "favicon.svg")
    create_placeholder_png(ASSETS / PLACEHOLDER_NAME)


def main() -> None:
    catalog = read_catalog()
    ensure_clean_dist()
    copy_static_assets()
    write_support_assets()
    write_catalog_files(catalog)
    write_summary_files(catalog)
    for variant in ["root-en", "en", "zh"]:
        write_posters_for_variant(catalog, variant)
        write_pages_for_variant(catalog, variant)
    print(f"Built Congo site into {DIST}")


if __name__ == "__main__":
    main()
