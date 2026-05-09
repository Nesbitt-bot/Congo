#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import textwrap
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
        "pickupNotes": "照片中包含包装盒。参考价采用 Lamicall 当前同类可折叠支架。",
    },
    "ikea-elloven-monitor-stand-drawer": {
        "name": "IKEA ELLOVEN 带抽屉显示器增高架",
        "description": "IKEA ELLOVEN 显示器增高架，竹制抽屉，白色台面，照片中可见展开状态与标签。",
        "pickupNotes": "包含两张照片：抽屉展开视图和产品标签/参考贴纸。",
    },
    "asus-vp28uqg-monitor-arm": {
        "name": "ASUS VP28UQG 28 英寸 4K 显示器（带桌夹支架）",
        "description": "ASUS VP28UQG 28 英寸 4K 显示器，已安装可调节桌夹支架，附带 DP 线。",
        "pickupNotes": "包含桌夹支架和一根 DisplayPort 线。三张照片：正面、背部/支架和型号标签。",
    },
    "flexispot-e7-standing-desk-govee": {
        "name": "FlexiSpot Pro 升降桌（E7）+ Govee RGBIC 桌面灯带",
        "description": "FlexiSpot Pro 升降桌（E7）套餐，包含照片中展示的 Govee RGBIC 桌面灯带。",
        "pickupNotes": "套餐包含 FlexiSpot E7 升降桌和桌面上的 Govee RGBIC 灯带。四张照片：已组装桌架、零件视图、整桌视图和配件近景。",
    },
    "big-joe-comfort-chair": {
        "name": "Big Joe 舒适懒人椅",
        "description": "Big Joe 风格黑色舒适豆袋/懒人椅。",
        "pickupNotes": "当前只有一张照片。参考价使用当前 Big Joe 同类懒人椅在售价格作为近似比较。",
    },
    "hp-envy-6155e-printer-bundle": {
        "name": "HP Envy 6155e 打印机套装",
        "description": "HP Envy 6155e 一体机套装，包含额外黑色墨盒和照片中展示的 HP Premium 24 打印纸。",
        "pickupNotes": "套装包含打印机、额外黑色墨盒和 HP Premium 24 打印纸。参考价采用 HP 官方当前打印机页面，耗材为额外赠送内容。",
    },
    "honeywell-quietset-8-fan": {
        "name": "Honeywell QuietSet 8 40英寸塔扇",
        "description": "Honeywell QuietSet 8 全房间 40 英寸塔扇，照片中带原包装箱。",
        "pickupNotes": "包含两张照片：带包装箱的整机图和顶部控制面板近景。",
    },
    "herman-miller-aeron-chair-size-b": {
        "name": "Herman Miller Aeron 人体工学椅（全功能，B号）",
        "description": "Herman Miller Aeron 人体工学椅，全功能配置，B 号尺寸。包含正面和侧面两张照片。",
        "pickupNotes": "包含两张照片。参考价格使用你提供的 SeatingMind 对应商品页面。",
    },
    "whiteboard-bundle-two-boards-markers": {
        "name": "两块白板 + 三色白板笔套装",
        "description": "套装包含两块可擦写白板，以及一组三色 Pilot V Board Master 白板笔。",
        "pickupNotes": "参考价格是根据相似 U Brands 白板和当前 Pilot V Board Master 白板笔套装做出的实用估算。",
    },
    "floor-lamp-generic": {
        "name": "落地灯",
        "description": "黑色落地灯，带两个白色灯罩，照片中为已组装并可正常使用状态。",
        "pickupNotes": "已补充实拍照片。标准双灯头落地灯。",
    },
    "ikea-skadis-pegboard-set": {
        "name": "IKEA SKÅDIS 洞洞板套装",
        "description": "IKEA SKÅDIS 白色洞洞板套装，包含挂篮、小盒、托盘、挂钩和夹具等配件，照片中展示为整套。",
        "pickupNotes": "隐藏售价尚未设置，因此该商品暂时仅展示不开放出价。",
    },
    "flexispot-slim-desk-drawer-s07lb": {
        "name": "FlexiSpot 超薄桌下收纳抽屉 S07LB",
        "description": "FlexiSpot 超薄桌下收纳抽屉，型号 S07LB，照片中展示原包装箱。",
        "pickupNotes": "当前只附带一张照片，商品展示为原包装箱状态。",
    },
    "frigidaire-gallery-mini-fridge": {
        "name": "Frigidaire Gallery 迷你美妆冰箱（6罐装）",
        "description": "Frigidaire Gallery 迷你美妆冰箱 / 小型冷藏箱，照片中展示了原包装盒和电源配件。",
        "pickupNotes": "照片中包含原包装箱和配件。属于小型台面迷你冰箱尺寸。",
    },
    "frigidaire-countertop-ice-maker": {
        "name": "Frigidaire 台面制冰机（每日 26 磅）",
        "description": "Frigidaire 台面制冰机，标称每日制冰 26 磅，照片中展示了原包装箱。",
        "pickupNotes": "照片中可见原包装箱。属于台面尺寸的小型制冰机。",
    },
    "goveelife-air-purifier-h7120": {
        "name": "GoveeLife 空气净化器 H7120",
        "description": "GoveeLife 空气净化器，型号 H7120，照片中展示了原包装箱。",
        "pickupNotes": "隐藏售价尚未设置，因此该商品目前以待定状态展示。",
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
        "pickupNotes": "当前只附带一张照片。属于紧凑型电视 / 媒体桌尺寸。",
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
                "最终结账页会自动生成一封发给 {email} 的预约邮件。",
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
            "checkoutDesc": "先解锁商品，再用这里生成自提或配送预约邮件。",
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


def create_poster_png(path: Path, *, site: dict, lang: str, title: str, subtitle_lines: list[str], footer: str, qr_target: str) -> None:
    qr_path = ensure_qr_png(qr_target)
    tmp = path.with_suffix(".tmp.png")
    caption = site["strings"]["posterQrCaption"]
    run_convert([
        "-size", "1200x630", "gradient:#131a22-#243b55",
        "-fill", "#f3a847", "-draw", "rectangle 0,0 1200,96",
        "-fill", "#131a22", "-font", str(FONT_BOLD), "-gravity", "northwest",
        "-pointsize", "42", "-annotate", "+56+26", site.get("title", "Congo"),
        "-fill", "white", "-font", str(FONT_BOLD), "-pointsize", "68",
        "-annotate", "+56+150", wrap_lines(title, 20, max_lines=1)[0],
        *(sum(([
            "-fill", "white" if idx == 0 else "white",
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
          <span class=\"brand-mark\">CO</span>
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
          {nav_link(page_root, s['homeNav'], '⌂', 'index')}
          {nav_link(page_root + 'about/', s['aboutNav'], 'ℹ', 'about')}
        </nav>
        <a class=\"cart-link compact\" href=\"{page_root}checkout/\" aria-label=\"{escape(s['cartNav'])}\">
          <span class=\"cart-icon\">🛒</span>
          <span class=\"cart-count-inline\">(<span data-cart-count>0</span>)</span>
        </a>
        <div class=\"language-switch\">
          <span class=\"language-switch-label\">{escape(s['langSwitchLabel'])}</span>
          <select class=\"language-select\" data-language-switch>
            <option value=\"{switch_en}\" {"selected" if current_lang == "en" else ""}>{escape(s['langEnglish'])}</option>
            <option value=\"{switch_zh}\" {"selected" if current_lang == "zh" else ""}>{escape(s['langChinese'])}</option>
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
    return f"""
    <main class=\"checkout-page\">
      <section class=\"cart-panel panel\">
        <div class=\"section-header\" style=\"margin-bottom:18px\">
          <div>
            <h1>{escape(s['checkoutTitle'])}</h1>
            <p>{escape(s['checkoutDesc'])}</p>
          </div>
          <button id=\"clear-cart\" class=\"btn-ghost\">{escape(s['clearCart'])}</button>
        </div>
        <div id=\"page-error\" class=\"status-box bad hide\"></div>
        <div id=\"cart-list\" class=\"cart-list\"></div>
      </section>
      <aside class=\"summary-card checkout-card\">
        <h2 class=\"block-title\">{escape(s['orderSummary'])}</h2>
        <div class=\"checkout-summary-rows\" style=\"margin:16px 0\">
          <div class=\"checkout-summary-row\"><span>{escape(s['itemsLabel'])}</span><strong id=\"summary-count\">0</strong></div>
          <div class=\"checkout-summary-row\"><span>{escape(s['totalLabel'])}</span><strong id=\"summary-total\">$0</strong></div>
        </div>
        <div class=\"progress\"><span id=\"delivery-progress\" style=\"width:0%\"></span></div>
        <div id=\"delivery-message\" class=\"status-box info\" style=\"margin-top:12px\">{escape(s['deliveryNeedMore'].format(amount=threshold))}</div>
        <p class=\"small-note\">{escape(s['checkoutAddressedTo'].format(email=site.get('contactEmail', '')))}</p>
        <form id=\"checkout-form\" class=\"checkout-form\">
          <div class=\"form-grid\">
            <input name=\"name\" placeholder=\"{escape(s['yourName'])}\" />
            <input name=\"email\" type=\"email\" placeholder=\"{escape(s['yourEmail'])}\" />
            <input name=\"phone\" placeholder=\"{escape(s['yourPhone'])}\" />
            <input name=\"when\" placeholder=\"{escape(s['preferredTime'])}\" />
          </div>
          <select name=\"deliveryMode\">
            <option>{escape(s['pickupOption'])}</option>
            <option>{escape(s['localDeliveryOption'])}</option>
            <option>{escape(s['eitherWorksOption'])}</option>
          </select>
          <input name=\"address\" placeholder=\"{escape(s['pickupPoint'])}\" />
          <textarea name=\"notes\" placeholder=\"{escape(s['notesPlaceholder'])}\"></textarea>
          <div class=\"inline-actions\">
            <button type=\"button\" id=\"copy-email\" class=\"btn-amazon\">{escape(s['copyEmailText'])}</button>
            <a id=\"open-mailto\" class=\"btn-secondary\" href=\"mailto:{contact_email}\">{escape(s['openEmailDraft'])}</a>
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


def summary_lines_for_catalog(catalog: dict, lang: str) -> str:
    localized = localize_catalog(catalog, lang)
    site = localized["site"]
    public = site.get("publicUrl", site.get("baseUrl", "https://nesbitt-bot.github.io/Congo")).rstrip("/")
    pickup = site.get("pickupAddress", "")
    is_zh = lang == "zh"
    intro = f"出二手 自取 {pickup}" if is_zh else f"Second-hand for sale · Pickup at {pickup}"
    site_url = f"{public}/{lang}/?mode=plain"
    site_line = f"最新页面：{site_url}" if is_zh else f"Latest update: {site_url}"
    sections = [intro, site_line, ""]
    for item in localized["items"]:
        if item.get("status") == "sold":
            continue
        price = item.get("actualPrice")
        price_label = (f"${int(price) if float(price).is_integer() else price}" if price is not None else ("待定" if is_zh else "Price pending"))
        item_url = f"{public}/{lang}/item/{item['id']}/?mode=plain"
        image_path = item.get("image") or (item.get("images") or ["assets/placeholder.png"])[0]
        image_url = f"{public}/{image_path.lstrip('/')}"
        sections.append(f"## [{item['name']}]({item_url}) ({price_label})")
        sections.append("")
        sections.append((f"最早可取：{item.get('earliestPickupDate', '')}" if is_zh else f"Earliest available: {item.get('earliestPickupDate', '')}"))
        if item.get('latestPickupDate'):
            sections.append((f"最晚可取：{item.get('latestPickupDate')}" if is_zh else f"Latest available: {item.get('latestPickupDate')}"))
        if item.get('pickupNotes'):
            sections.append((f"附加信息：{item.get('pickupNotes')}" if is_zh else f"Additional info: {item.get('pickupNotes')}"))
        sections.append("")
        sections.append(f"![{item['name']}]({image_url})")
        sections.append("")
    return "\n".join(sections).strip() + "\n"


def write_summary_files(catalog: dict) -> None:
    summary_dir = ROOT / "summary"
    summary_dir.mkdir(parents=True, exist_ok=True)
    (summary_dir / "summary.en.md").write_text(summary_lines_for_catalog(catalog, "en"), encoding="utf-8")
    (summary_dir / "summary.zh.md").write_text(summary_lines_for_catalog(catalog, "zh"), encoding="utf-8")


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
