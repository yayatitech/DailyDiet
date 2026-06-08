import ReactMarkdown from "react-markdown";
import remarkBreaks from "remark-breaks";

type Props = {
  markdown: string;
};

export default function RecipeInstructions({ markdown }: Props) {
  return (
    <div className="recipe-instructions">
      <ReactMarkdown remarkPlugins={[remarkBreaks]}>{markdown}</ReactMarkdown>
    </div>
  );
}
