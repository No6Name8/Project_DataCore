import { useLang } from "../i18n/LanguageContext";
export default function Benefits() {
  const { isRTL } = useLang();
  return (
    <div className="flex items-center justify-center min-h-96">
      <div className="text-center space-y-2">
        <div className="text-4xl font-bold text-gold-gradient">Benefits</div>
        <div className="text-gray-400 text-sm">Coming next</div>
      </div>
    </div>
  );
}
