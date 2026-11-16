import type {ComponentType} from 'react';

// Original SVG glyphs: solid silhouettes and heavier details for the iOS UI.
// No Apple symbol font or exported SF Symbols assets are bundled.
const paths = {
 camera:'M7 2h10l2 3h3a2 2 0 0 1 2 2v13a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h3Zm5 5a6 6 0 1 0 0 12 6 6 0 0 0 0-12Zm0 3a3 3 0 1 1 0 6 3 3 0 0 1 0-6Z',
 book:'M1 1h8a4 4 0 0 1 3 2 4 4 0 0 1 3-2h8v19h-8a3 3 0 0 0-3 3 3 3 0 0 0-3-3H1Zm3 4v2h5V5Zm0 5v2h5v-2Zm11-5v2h5V5Zm0 5v2h5v-2Z',
 chart:'M1 1h3v19h19v3H1Zm4 14 6-7 5 4 5-8 3 2-7 11-5-4-5 5Z',
 notes:'M3 0h18a2 2 0 0 1 2 2v20a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2Zm3 5v2h12V5Zm0 5v2h12v-2Zm0 5v2h8v-2Z',
 shield:'M12 0 23 4v7c0 6-5 10-11 13C6 21 1 17 1 11V4Zm-5 10-2 2 5 5 9-9-2-2-7 7Z',
 brain:'M12 0C5 0 2 5 2 11v2l-2 4h4v4h5v3h11V13C26 6 20 0 12 0Zm-3 4a2 2 0 0 1 3 0 2 2 0 0 1 4 1 2 2 0 0 1 1 4 2 2 0 0 1-1 4h-2v-3h-2v4H9v-3H7V8h2V6H7a2 2 0 0 1 2-2Z',
 thermometer:'M8 4a4 4 0 0 1 8 0v10a6 6 0 1 1-8 0Zm3 0v11l-1 1a3 3 0 1 0 4 0l-1-1V4Z',
 sliders:'M0 4h3a4 4 0 0 1 8 0h13v3H11a4 4 0 0 1-8 0H0Zm0 13h13a4 4 0 0 1 8 0h3v3h-3a4 4 0 0 1-8 0H0Z',
 scissors:'M5 0a5 5 0 1 0 3 9l3 3-3 3a5 5 0 1 0 2 3l4-4 8 8 2-2-8-8 8-8-2-2-8 8-4-4A5 5 0 0 0 5 0Zm0 3a2 2 0 1 1 0 4 2 2 0 0 1 0-4Zm0 14a2 2 0 1 1 0 4 2 2 0 0 1 0-4Z',

 water: 'M12 1C9 6 4 10 4 15a8 8 0 0 0 16 0c0-5-5-9-8-14Z',
 sparkles: 'm14 2 2.4 7.6L23 12l-6.6 2.4L14 22l-2.4-7.6L5 12l6.6-2.4ZM5 1l1.3 3.7L10 6 6.3 7.3 5 11 3.7 7.3 0 6l3.7-1.3Z',
 health: 'M11 23V13C5 13 2 9 3 3c3 0 4 1 6 3l3-5 3 5c2-2 3-3 6-3 1 6-2 10-8 10v6c2-4 5-5 9-5-1 6-4 8-9 8v1Zm-2-3c-5 0-8-3-8-7 5 0 7 2 8 7Z',
 sun: 'M12 5a7 7 0 1 0 0 14 7 7 0 0 0 0-14ZM11 0h2v3h-2Zm0 21h2v3h-2ZM0 11h3v2H0Zm21 0h3v2h-3ZM3 1.6 5.4 4 4 5.4 1.6 3Zm15.6 17L20 17.2l2.4 2.4-1.4 1.4ZM1.6 21 4 18.6 5.4 20 3 22.4ZM18.6 4 21 1.6 22.4 3 20 5.4Z',
 leaf: 'M2 2c8 3 17-2 20 17-7 4-19 2-20-17Zm3 4c3 7 8 9 14 12l1-2C13 14 9 11 5 6Z',
 home: 'm12 1 12 10-2 2-2-1.7V23h-6v-8h-4v8H4V11.3L2 13l-2-2Z',
 calendar: 'M5 0h3v3h8V0h3v3h2a2 2 0 0 1 2 2v17a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h2Zm-1 9v12h16V9Zm2 2h3v3H6Zm5 0h3v3h-3Zm5 0h2v3h-2ZM6 16h3v3H6Zm5 0h3v3h-3Zm5 0h2v3h-2Z',
 flask: 'M8 0h8v3h-1v6l8 12a2 2 0 0 1-2 3H3a2 2 0 0 1-2-3L9 9V3H8Zm3 3v7l-3 5h8l-3-5V3Z',
 more: 'M12 0a12 12 0 1 0 0 24 12 12 0 0 0 0-24ZM5 10a2 2 0 1 1 0 4 2 2 0 0 1 0-4Zm7 0a2 2 0 1 1 0 4 2 2 0 0 1 0-4Zm7 0a2 2 0 1 1 0 4 2 2 0 0 1 0-4Z',
 grid: 'M3 0h5a3 3 0 0 1 3 3v5a3 3 0 0 1-3 3H3a3 3 0 0 1-3-3V3a3 3 0 0 1 3-3Zm13 0h5a3 3 0 0 1 3 3v5a3 3 0 0 1-3 3h-5a3 3 0 0 1-3-3V3a3 3 0 0 1 3-3ZM3 13h5a3 3 0 0 1 3 3v5a3 3 0 0 1-3 3H3a3 3 0 0 1-3-3v-5a3 3 0 0 1 3-3Zm13 0h5a3 3 0 0 1 3 3v5a3 3 0 0 1-3 3h-5a3 3 0 0 1-3-3v-5a3 3 0 0 1 3-3Z',
 qr: 'M0 0h10v10H0Zm3 3v4h4V3ZM14 0h10v10H14Zm3 3v4h4V3ZM0 14h10v10H0Zm3 3v4h4v-4ZM14 14h4v4h-4Zm6 0h4v4h-4Zm-6 6h4v4h-4Zm6 0h4v4h-4Z',
 rotate: 'M12 3a9 9 0 1 1-9 9h3a6 6 0 1 0 6-6v4L5 4l7-4Z',
 box: 'm12 0 12 6v12l-12 6-12-6V6Zm0 3L4 7l8 4 8-4ZM3 9v7l7.5 3.8v-7ZM13.5 13v6.8L21 16V9Z',
 pin: 'M12 0a8 8 0 0 0-8 8c0 6 8 16 8 16s8-10 8-16a8 8 0 0 0-8-8Zm0 5a3 3 0 1 1 0 6 3 3 0 0 1 0-6Z',
} as const;
export type IOSIconName = keyof typeof paths;
export function IOSIcon({name,size=24,className=''}:{name:IOSIconName;size?:number;className?:string}){
 return <svg aria-hidden="true" focusable="false" width={size} height={size} viewBox="0 0 24 24" fill="currentColor" className={`ios-symbol ${className}`}><path d={paths[name]} fillRule="evenodd"/></svg>;
}
export const iosNavigation:Record<string,IOSIconName>={today:'home',plants:'leaf',care:'calendar',products:'flask',more:'more'};
export const iosTools:Record<string,IOSIconName>={ai:'brain',labels:'qr',guides:'book',diagnosis:'shield',identify:'camera',catalog:'leaf',species:'book',sensors:'thermometer',backup:'box',settings:'sliders'};
export function adaptiveIcon(name:IOSIconName,Fallback:ComponentType<{size?:number;className?:string}>){
 return function AdaptiveIcon({size=24,className=''}:{size?:number;className?:string}){return <><Fallback size={size} className={`desktop-symbol ${className}`}/><IOSIcon name={name} size={size} className={`mobile-symbol ${className}`}/></>};
}
