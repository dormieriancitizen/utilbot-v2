import asyncio
from io import BytesIO
from pathlib import Path
import re
import discord
from discord.ext import commands

START_CODE_BLOCK_RE = re.compile(r"^((```(la)?tex)(?=\s)|(```))")


class TexCommands(commands.Cog):
    """Commands to deal with the sending/recieving/editing of messages"""

    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @staticmethod
    def cleanup_code(content: str):
        """Automatically removes code blocks from the code."""
        if content.startswith("```") and content.endswith("```"):
            return START_CODE_BLOCK_RE.sub("", content)[:-3]

        return content.strip("` \n")

    @staticmethod
    async def latex_to_buf(tex: str) -> BytesIO | str:
        tmp_dir = Path("/tmp")
        output_filename = tmp_dir / "latex"

        async def pdf_to_png(pdf_path: Path, dpi=300) -> BytesIO:
            output_png = tmp_dir / "output.png"

            gs_command = [
                "gs",
                "-dNOPAUSE",
                "-dBATCH",
                "-sDEVICE=png16m",
                f"-r{dpi}",
                "-dTextAlphaBits=4",
                "-dGraphicsAlphaBits=4",
                f"-sOutputFile={output_png}",
                str(pdf_path),
            ]

            process = await asyncio.create_subprocess_exec(
                *gs_command,
                stdout=asyncio.subprocess.DEVNULL,  # discard stdout
                stderr=asyncio.subprocess.PIPE,  # capture stderr for errors
            )

            _, stderr = await process.communicate()

            if process.returncode != 0:
                raise RuntimeError

            try:
                with output_png.open("rb") as f:
                    png_bytes = f.read()
            finally:
                output_png.unlink(missing_ok=True)

            img_buffer = BytesIO(png_bytes)
            img_buffer.seek(0)
            return img_buffer

        print(f"Trying to render the following tex: {tex}")

        tex_file = output_filename.with_suffix(".tex")
        tex_file.write_text(tex, encoding="utf-8")

        try:
            process = await asyncio.create_subprocess_exec(
                "pdflatex",
                "-interaction=nonstopmode",
                str(tex_file),
                cwd=str(tmp_dir),
                stdout=asyncio.subprocess.DEVNULL,
            )

            await process.wait()

            if process.returncode != 0:
                return output_filename.with_suffix(".log").read_text()
        except Exception as error:
            return f"Error running pdflatex: {error}"

        pdf_file = output_filename.with_suffix(".pdf")

        try:
            img_buffer = await pdf_to_png(pdf_file, dpi=300)
        except RuntimeError:
            return "Error while running ghostscript"

        for ext in [".aux", ".log", ".pdf", ".tex"]:
            try:
                (output_filename.with_suffix(ext)).unlink()
            except FileNotFoundError:
                pass

        return img_buffer

    @commands.command()
    async def tex(self, ctx: commands.Context, *, body: str):
        tex = self.cleanup_code(body)

        full_tex = (
            r"""
\documentclass[preview,border=5pt]{standalone}
\usepackage{amsmath}
\begin{document}
$
\begin{aligned}
"""
            + tex
            + r"""
\end{aligned}
$
\end{document}
"""
        )

        file = await self.latex_to_buf(full_tex)
        if isinstance(file, str):
            await ctx.reply("LaTeX failed to render")
            print(file)
            return
        await ctx.send(file=discord.File(fp=file, filename="tex.png"))

    @commands.command()
    async def plot(self, ctx: commands.Context, *, body: str):
        tex = self.cleanup_code(body)

        full_tex = (
            r"""
\documentclass[preview,border=5pt]{standalone}
\usepackage{amsmath}
\usepackage{pgfplots}
\begin{document}
\begin{tikzpicture}
    \begin{axis}
        \addplot[color=red]{
"""
            + tex
            + r"""
};
    \end{axis}
\end{tikzpicture}
\end{document}
"""
        )

        file = await self.latex_to_buf(full_tex)
        if isinstance(file, str):
            await ctx.reply("LaTeX failed to render")
            print(file)
            return
        await ctx.send(file=discord.File(fp=file, filename="tex.png"))


async def setup(bot):
    await bot.add_cog(TexCommands(bot))
