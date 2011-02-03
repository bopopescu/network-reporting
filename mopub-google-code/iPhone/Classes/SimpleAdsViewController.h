//
//  SimpleAdsViewController.h
//  Copyright (c) 2010 MoPub Inc.
//
//

#import <UIKit/UIKit.h>
#import "AdController.h"
#import "InterstitialAdController.h"
#import "SecondViewController.h"

#define PUB_ID_320x50 @"agltb3B1Yi1pbmNyDAsSBFNpdGUYkaoMDA"
#define PUB_ID_300x250 @"agltb3B1Yi1pbmNyDAsSBFNpdGUYycEMDA"
#define PUB_ID_INTERSTITIAL @"agltb3B1Yi1pbmNyDAsSBFNpdGUYsckMDA"
#define PUB_ID_NAV_INTERSTITIAL @"agltb3B1Yi1pbmNyDAsSBFNpdGUYsbcSDA"


@class InterstitialAdController;

@interface SimpleAdsViewController : UIViewController <UITextFieldDelegate, InterstitialAdControllerDelegate> {
	IBOutlet UITextField* keyword;
	IBOutlet UIView* adView;
	IBOutlet UIView* mrectView;
	
	BOOL getAndShow;
	
	AdController* adController;
	AdController* mrectController;
	InterstitialAdController *interstitialAdController;
	InterstitialAdController *navigationInterstitialAdController;
	
	BOOL shownNavigationInterstitialAlready;

}
@property(nonatomic,retain) IBOutlet UITextField* keyword;
@property(nonatomic,retain) IBOutlet UIView* adView;
@property(nonatomic,retain) IBOutlet UIView* mrectView;
@property(nonatomic,retain) AdController* adController;
@property(nonatomic,retain) AdController* mrectController;
@property(nonatomic,retain) InterstitialAdController* interstitialAdController;
@property(nonatomic,retain) InterstitialAdController* navigationInterstitialAdController;

-(IBAction) refreshAd;
-(IBAction) showModalInterstitial;
-(IBAction) getModalInterstitial;
-(IBAction) getAndShowModalInterstitial;
-(IBAction) getNavigationInterstitial;

- (void)adjustAdSize;

@end

